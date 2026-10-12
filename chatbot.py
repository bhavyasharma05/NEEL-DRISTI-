import os
import json
import pandas as pd
import numpy as np
import faiss
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.oauth2 import service_account
from google.cloud import bigquery
from sentence_transformers import SentenceTransformer
from google.api_core import exceptions as google_exceptions
import math
from io import StringIO
import plotly.express as px
import base64
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import threading
import requests
from fastapi.responses import StreamingResponse
import asyncio
import cohere

# Load environment variables
load_dotenv()

# Configure Cohere API
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
if not COHERE_API_KEY:
    raise RuntimeError("COHERE_API_KEY environment variable not set in .env file.")

# Cohere client will be initialized at startup
# (declared here so other functions can reference it)
cohere_client = None

# --- Configuration ---
# Default values (can be overridden by env vars or service account file)
PROJECT_ID = os.getenv("BQ_PROJECT_ID", "floatchat-472116")
DATASET_ID = os.getenv("BQ_DATASET_ID", "argo")
TABLE_NAME = os.getenv("BQ_TABLE_NAME", "argo_profiles")
EMBEDDING_MODEL_NAME = os.getenv('EMBEDDING_MODEL_NAME', 'paraphrase-multilingual-MiniLM-L12-v2')
BQ_SAMPLE_LIMIT = int(os.getenv("BQ_SAMPLE_LIMIT", "10000"))
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "128"))
ALLOW_ASK_BEFORE_READY = os.getenv("ALLOW_ASK_BEFORE_READY", "true").lower() in ("1", "true", "yes")
MAX_QUERY_ROWS = int(os.getenv("MAX_QUERY_ROWS", "1000"))
DEFAULT_TIME_INTERVAL_DAYS = int(os.getenv("DEFAULT_TIME_INTERVAL_DAYS", "180"))
# Path to GCP service account key: prefer env var if valid, else fallback to local file
_env_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if _env_credentials_path:
    # Trim accidental quotes/spaces often present in Windows env var values
    _env_credentials_path = _env_credentials_path.strip().strip('"').strip("'")

_default_credentials_path_1 = os.path.join(os.path.dirname(__file__), "floatchat-key.json")

_candidates = [
    _env_credentials_path if _env_credentials_path else None,
    _default_credentials_path_1,
]
_candidates = [p for p in _candidates if p]

SERVICE_ACCOUNT_FILE = None
for _p in _candidates:
    if os.path.exists(_p):
        SERVICE_ACCOUNT_FILE = _p
        break

if not SERVICE_ACCOUNT_FILE:
    raise RuntimeError(
        "Google service account file not found. "
        f"Checked: {', '.join(_candidates)}. "
        "Set GOOGLE_APPLICATION_CREDENTIALS to a valid JSON key path or place floatchat-key.json in the project root."
    )

# If no explicit BQ project override, infer from the service account JSON
if not os.getenv("BQ_PROJECT_ID"):
    try:
        with open(SERVICE_ACCOUNT_FILE, "r", encoding="utf-8") as _f:
            _sa = json.load(_f)
            _proj_from_key = _sa.get("project_id")
            if _proj_from_key:
                PROJECT_ID = _proj_from_key
    except Exception:
        # Non-fatal; keep the default PROJECT_ID
        pass

# --- Globals ---
bq_client = None
llm = None
embedding_model = None
faiss_index = None
descriptions = None
is_ready = False
_qa_cache: dict[str, tuple[str, float]] = {}
_cache_ttl_seconds = int(os.getenv("QA_CACHE_TTL_SECONDS", "300"))

# Add conversation history storage (session_id -> list of messages)
_conversation_history: dict[str, list[dict]] = {}
MAX_HISTORY_LENGTH = 10  # Keep last 10 messages per session

def initialize_vector_store():
    """Loads data and builds the vector store in a separate thread."""
    global faiss_index, descriptions, is_ready
    print("Background initialization started...")
    try:
        df = load_data_from_bq(bq_client)
        faiss_index, descriptions = create_vector_store(df, embedding_model)
        is_ready = True
        print("Background initialization complete. Server is ready.")
    except Exception as e:
        print(f"Error during background initialization: {e}")
        # You might want to handle this more gracefully
        is_ready = False

def call_cohere_api(text_prompt: str, max_tokens: int = 512, temperature: float = 0.2, stream: bool = False):
    """Call Cohere Chat API via the official SDK client.

    Returns the generated text (non-streaming) or a generator (streaming).
    """
    global cohere_client
    if cohere_client is None:
        raise RuntimeError("Cohere client not initialized")

    try:
        if stream:
            # Use chat_stream for streaming responses
            resp = cohere_client.chat_stream(
                model="command-r-plus-08-2024",  # Current Cohere model as of Oct 2025
                message=text_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            # Return the streaming generator directly
            return resp
        else:
            # Use regular chat for non-streaming responses
            resp = cohere_client.chat(
                model="command-r-plus-08-2024",
                message=text_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            
            # Extract text from non-streaming response
            if hasattr(resp, 'text'):
                return resp.text
            elif hasattr(resp, 'message'):
                return resp.message
            else:
                # Fallback: try to access as dict
                if isinstance(resp, dict):
                    return resp.get('text', '') or resp.get('message', '')
                return str(resp)
    except Exception as e:
        print(f"Cohere API call failed: {e}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initializes services and starts the vector store creation in the background.
    """
    global bq_client, embedding_model, cohere_client
    print("Application startup...")
    
    # Initialize connections and models
    print("Initializing BigQuery client and embedding model...")
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    bq_client = bigquery.Client(credentials=credentials, project=PROJECT_ID)
    
    # Initialize Cohere client and test connection
    try:
        cohere_client = cohere.Client(COHERE_API_KEY)
        test_response = call_cohere_api("Test connection", max_tokens=10)
        print("Cohere API initialized successfully")
    except Exception as e:
        print(f"Failed to initialize Cohere API: {e}")
        raise
    
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    
    # Start background initialization
    initialization_thread = threading.Thread(target=initialize_vector_store)
    initialization_thread.start()
    
    print("Application startup complete. Vector store is building in the background.")
    yield
    print("Application shutdown.")

# --- FastAPI App Setup ---
app = FastAPI(
    title="Argo RAG Chatbot Backend",
    description="A backend service for querying Argo float data using a RAG pipeline.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class QueryRequest(BaseModel):
    question: str
    session_id: str | None = None  # Add session tracking

class QueryResponse(BaseModel):
    answer: str
    generated_sql: str
    session_id: str | None = None  # Return session ID

class ReadyResponse(BaseModel):
    status: str

class QueryWithDataResponse(BaseModel):
    answer: str
    generated_sql: str
    data: list
    chart_png_b64: str | None = None

class InsightsRequest(BaseModel):
    time_range: str | None = None  # e.g., '1m','3m','6m','1y'
    region: str | None = None      # 'global','atlantic','pacific','indian'

class TemperatureDepthPoint(BaseModel):
    depth: float
    temperature: float

class SalinityDepthPoint(BaseModel):
    depth: float
    salinity: float
    pressure: float

class PressureDepthPoint(BaseModel):
    depth: float
    pressure: float

# --- Helper Functions ---

def load_data_from_bq(client):
    """Loads a sample of the data from BigQuery."""
    print("Loading data from BigQuery for vector store...")
    query = f"""
    SELECT
        timestamp,
        lat,
        lon,
        temperature
    FROM
        `{PROJECT_ID}.{DATASET_ID}.{TABLE_NAME}`
    ORDER BY
        timestamp DESC
    LIMIT {BQ_SAMPLE_LIMIT}
    """
    try:
        df = client.query(query).to_dataframe()
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df.dropna(subset=['timestamp', 'lat', 'lon', 'temperature'], inplace=True)
        print("Data loaded successfully.")
        return df
    except Exception as e:
        print(f"Failed to load data from BigQuery: {e}")
        raise

def create_vector_store(df, model):
    """Creates a FAISS vector store from the dataframe."""
    if df.empty:
        return None, None
    
    print("Creating vector store...")
    df['description'] = df.apply(
        lambda row: f"Measurement taken on {row['timestamp'].strftime('%Y-%m-%d')} at location ({row['lat']:.2f}, {row['lon']:.2f}) with a temperature of {row['temperature']:.2f}°C.",
        axis=1
    )
    
    doc_list = df['description'].tolist()
    embeddings = model.encode(
        doc_list,
        show_progress_bar=False,
        batch_size=EMBEDDING_BATCH_SIZE,
        convert_to_numpy=True,
        normalize_embeddings=True
    )
    
    dimension = embeddings.shape[1]
    # Using Inner Product with normalized vectors equals cosine similarity
    index = faiss.IndexFlatIP(dimension)
    index.add(np.array(embeddings, dtype='float32'))
    
    print("Vector store created successfully.")
    return index, doc_list

# --- RAG Core Functions ---

def find_relevant_profiles(user_query, top_k=5):
    """Finds the most relevant profile descriptions from the vector store."""
    query_embedding = embedding_model.encode([user_query])
    _, indices = faiss_index.search(np.array(query_embedding, dtype='float32'), top_k)
    return [descriptions[i] for i in indices[0]]

def generate_sql_query(user_query, relevant_profiles, conversation_context: str = ""):
    """Generates a BigQuery SQL query using Gemini 2.0 Flash with conversation context."""
    schema = """
    - timestamp (STRING, format: YYYY-MM-DD HH:MM:SS UTC)
    - lat (FLOAT)
    - lon (FLOAT)
    - pressure (FLOAT)
    - temperature (FLOAT)
    - salinity (FLOAT)
    - depth_m (FLOAT)
    """
    
    context_instruction = ""
    if conversation_context:
        context_instruction = f"""
**Previous Conversation:**
{conversation_context}

Use the conversation history to understand context. For example:
- If user says "what about last year?" refer to the parameter from previous question
- If user says "compare that with..." use the previous location/time
- Maintain continuity with previous queries
"""
    
    prompt = f"""
You are an expert BigQuery SQL generator. Generate a single, executable SQL query based on the user's question, context, and conversation history.

**BigQuery Table Schema:**
Table: `{PROJECT_ID}.{DATASET_ID}.{TABLE_NAME}`
Columns:
{schema}

**Context from similar measurements:**
{relevant_profiles}

{context_instruction}

**Current User Question:**
"{user_query}"

**Instructions:**
1. Generate a BigQuery SQL query that answers the current question
2. Use conversation history to resolve references like "that", "same location", "previous", etc.
3. Use exact table and column names from schema
4. For time queries, ALWAYS use DAY intervals (not MONTH or YEAR):
   - "last week" → WHERE CAST(timestamp AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
   - "last month" → WHERE CAST(timestamp AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
   - "last 3 months" → WHERE CAST(timestamp AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
   - "last 6 months" → WHERE CAST(timestamp AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 180 DAY)
   - "last year" → WHERE CAST(timestamp AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 365 DAY)
   - "this year" → WHERE CAST(timestamp AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 365 DAY)
5. NEVER use INTERVAL with MONTH or YEAR - only use DAY
6. Return only the raw SQL query, no explanations or markdown

**Generated SQL Query:**
"""
    
    try:
        response_text = call_cohere_api(prompt)
        raw_sql = response_text.strip().replace('```sql', '').replace('```', '')
        return optimize_sql_query(raw_sql)
    except Exception as e:
        print(f"Error generating SQL query: {e}")
        raise

def run_bq_query(sql_query):
    """Executes the BigQuery query and returns the result as a DataFrame."""
    try:
        print("Executing generated SQL query in BigQuery...")
        query_job = bq_client.query(sql_query)
        return query_job.to_dataframe()
    except Exception as e:
        print(f"BigQuery query failed for query:\n{sql_query}")
        print(f"Error: {e}")
        raise

def generate_summary(user_query, results_df, conversation_context: str = "", stream: bool = False):
    """Generates a natural language summary with conversation context."""
    print(f"\n{'='*80}")
    print(f"📝 GENERATING SUMMARY FOR USER")
    print(f"{'='*80}")
    print(f"Question: {user_query}")
    print(f"Data rows: {len(results_df) if results_df is not None else 0}")
    print(f"Has conversation context: {bool(conversation_context)}")
    
    if results_df is None or results_df.empty:
        response = "I couldn't find any data for your question. You might want to try rephrasing it or adjusting the time range."
        print(f"⚠️  No data found")
        print(f"Response: {response}")
        print(f"{'='*80}\n")
        return response

    try:
        # Calculate statistics for the prompt
        stats = {}
        
        # Time range
        time_info = ""
        if 'timestamp' in results_df.columns:
            try:
                times = pd.to_datetime(results_df['timestamp'], errors='coerce')
                if times.notna().any():
                    tmin = times.min()
                    tmax = times.max()
                    time_info = f"from {tmin.strftime('%B %d, %Y')} to {tmax.strftime('%B %d, %Y')}"
                    print(f"📅 Time range: {time_info}")
            except Exception:
                pass
        
        # Calculate stats for each parameter
        if 'temperature' in results_df.columns:
            temp = results_df['temperature'].dropna()
            if len(temp) > 0:
                stats['temperature'] = {
                    'min': temp.min(),
                    'max': temp.max(),
                    'avg': temp.mean(),
                    'unit': '°C'
                }
                print(f"🌡️  Temperature: {stats['temperature']['min']:.2f} to {stats['temperature']['max']:.2f} °C (avg: {stats['temperature']['avg']:.2f} °C)")
        
        if 'salinity' in results_df.columns:
            sal = results_df['salinity'].dropna()
            if len(sal) > 0:
                stats['salinity'] = {
                    'min': sal.min(),
                    'max': sal.max(),
                    'avg': sal.mean(),
                    'unit': 'PSU'
                }
                print(f"🌊 Salinity: {stats['salinity']['min']:.2f} to {stats['salinity']['max']:.2f} PSU (avg: {stats['salinity']['avg']:.2f} PSU)")
        
        if 'pressure' in results_df.columns:
            pres = results_df['pressure'].dropna()
            if len(pres) > 0:
                stats['pressure'] = {
                    'min': pres.min(),
                    'max': pres.max(),
                    'avg': pres.mean(),
                    'unit': 'dbar'
                }
                print(f"📊 Pressure: {stats['pressure']['min']:.1f} to {stats['pressure']['max']:.1f} dbar (avg: {stats['pressure']['avg']:.1f} dbar)")
        
        # Build a concise stats summary for the prompt
        stats_text = f"Found {len(results_df)} measurements"
        if time_info:
            stats_text += f" {time_info}"
        
        for param, data in stats.items():
            stats_text += f"\n{param.capitalize()}: {data['min']:.2f} to {data['max']:.2f} {data['unit']} (avg: {data['avg']:.2f} {data['unit']})"
        
        # Prepare conversation context instruction
        context_instruction = ""
        if conversation_context:
            context_instruction = f"**Previous Conversation:**\n{conversation_context}\n\nUse the conversation history to understand context."

        print(f"\n🤖 Calling Cohere API to generate natural language response...")

        # Generate natural language response
        prompt = f"""
You are Neel Drishti, a friendly oceanography assistant.
IMPORTANT: Your name is Neel Drishti. NEVER refer to yourself as OceanIQ.
Answer naturally with conversation context.

{context_instruction}

**Current Question:** "{user_query}"

**Data summary:**
{stats_text}

**Instructions:**
- Write 1-2 natural sentences answering the question
- If this relates to previous questions, acknowledge that connection
- Use specific numbers from the data
- Include units (°C, PSU, dbar)
- Be conversational

Your response:
"""

        response = call_cohere_api(prompt, stream=stream)
        
        if stream:
            # Return the stream generator directly for streaming mode
            return response
        
        # Non-streaming mode: process the complete response
        response = response.strip()

        print(f"\n✅ AI Response Generated:")
        print(f"┌{'─'*78}┐")
        for line in response.split('\n'):
            print(f"│ {line:<76} │")
        print(f"└{'─'*78}┘")
        print(f"{'='*80}\n")

        return response
    except Exception as e:
        print(f"\n❌ ERROR generating summary: {str(e)}")
        print(f"{'='*80}\n")
        return f"I found {len(results_df)} measurements for your query."

def _basic_stats_summary(user_query, df):
    """Fallback summarization without LLM."""
    try:
        parts = []
        
        # Add a natural opening
        parts.append(f"Here's what I found for your question:")
        
        # Time range
        if 'timestamp' in df.columns:
            try:
                tmin = pd.to_datetime(df['timestamp'], errors='coerce').min()
                tmax = pd.to_datetime(df['timestamp'], errors='coerce').max()
                if pd.notna(tmin) and pd.notna(tmax):
                    parts.append(f"\n📅 Period: {tmin.strftime('%b %d, %Y')} to {tmax.strftime('%b %d, %Y')}")
            except Exception:
                pass
        
        # Temperature
        if 'temperature' in df.columns:
            try:
                temp = df['temperature'].dropna()
                if len(temp) > 0:
                    parts.append(f"\n🌡️ Temperature: {temp.min():.2f}°C to {temp.max():.2f}°C (avg: {temp.mean():.2f}°C)")
            except Exception:
                pass
        
        # Salinity
        if 'salinity' in df.columns:
            try:
                sal = df['salinity'].dropna()
                if len(sal) > 0:
                    parts.append(f"\n🌊 Salinity: {sal.min():.2f} to {sal.max():.2f} PSU (avg: {sal.mean():.2f} PSU)")
            except Exception:
                pass
        
        # Pressure
        if 'pressure' in df.columns:
            try:
                pres = df['pressure'].dropna()
                if len(pres) > 0:
                    parts.append(f"\n📊 Pressure: {pres.min():.1f} to {pres.max():.1f} dbar (avg: {pres.mean():.1f} dbar)")
            except Exception:
                pass
        
        parts.append(f"\n📈 Total records: {len(df)}")
        
        return "".join(parts)
    except Exception:
        return f"I found {len(df)} measurements for your query."

def _usage_help() -> str:
    return (
        "Send your question in any language via: "
        "1) JSON: {\"question\":\"...\"} or {\"message\":\"...\"}, "
        "2) Form: 'question' (or q/query/message/text/prompt), "
        "3) Plain text body, or "
        "4) GET /ask?question=...\n"
        "Examples:\n"
        "- POST text/plain: '¿Cuál es la temperatura media en 2023?'\n"
        "- POST application/json: {\"question\":\"最新の温度データ\"}\n"
        "- GET /ask?question=latest+temperature"
    )


# --- Intent detection and general QA ---
def classify_intent(user_query: str) -> str:
    """Returns 'DATA' if the question needs database retrieval, else 'KNOWLEDGE'."""
    try:
        prompt = (
            "Classify the user's question for an ocean data assistant. "
            "Return exactly one token: DATA if answering requires querying observational datasets "
            "(e.g., specific time ranges, locations, aggregations, 'show', 'trend', 'near', 'between', "
            "'last N days/weeks/months/years', 'this week/month/year', 'in 2023', 'during', temporal references), "
            "otherwise KNOWLEDGE for general oceanography concepts or definitions.\n\n"
            f"Question: {user_query}\nAnswer: "
        )
        response_text = call_cohere_api(prompt)
        text = response_text.strip().upper()
        return "DATA" if "DATA" in text[:10] else "KNOWLEDGE"
    except Exception:
        # Safe default: try data path only if the query clearly looks like data
        lower_q = user_query.lower()
        data_keywords = ["show", "trend", "last", "near", "between", "average", "max", "min", "count", 
                        "where", "latitude", "longitude", "temperature", "salinity", "pressure", "time",
                        "week", "month", "year", "day", "this", "past", "recent", "latest",
                        "in 2023", "in 2024", "during", "from", "to", "since"]
        return "DATA" if any(k in lower_q for k in data_keywords) else "KNOWLEDGE"


def answer_general_question(user_query: str, stream: bool = False):
    """Use LLM to answer conceptual questions without hitting the database."""
    prompt = f"""
    You are Neel Drishti, a friendly and helpful oceanography assistant.
    IMPORTANT: Your name is Neel Drishti. NEVER introduce yourself as OceanIQ or any other name.
    
    Answer clearly and accurately in the user's language.
    Focus on ARGO floats, physical oceanography, and BGC (biogeochemical) parameters when relevant.

    User question:
    {user_query}

    Requirements:
    - Provide a concise explanation and practical context.
    - If the term is an acronym (e.g., BGC), expand it and list key parameters.
    - Avoid fabricating numeric results from datasets.
    - Use short paragraphs or bullet points.
    """
    try:
        response = call_cohere_api(prompt, stream=stream)
        if stream:
            # Return the stream generator directly
            return response
        else:
            # Return the text string
            return response.strip()
    except Exception as e:
        print(f"General QA failed: {e}")
        fallback = "I can explain oceanography terms (e.g., salinity, BGC parameters) and how ARGO floats measure them. Please try again."
        if stream:
            # Return a simple generator for fallback
            def fallback_gen():
                yield fallback
            return fallback_gen()
        return fallback


def optimize_sql_query(sql_query: str) -> str:
    """Clamp result size and add a default recent time window if missing to speed up queries."""
    sql = sql_query.strip().rstrip(';')
    lowered = sql.lower()
    
    # Only add default time window if NO time filter exists at all
    has_time_filter = any(keyword in lowered for keyword in [
        'time__utc_', 'timestamp', 'interval', 'date_sub', 'timestamp_sub', 
        'date(', 'datetime(', 'between', 'extract(', 'where'
    ])
    
    # If there's already a WHERE clause with time filtering, don't add another
    if not has_time_filter or ('where' not in lowered and 'timestamp' not in lowered):
        if ' where ' in lowered:
            # Find the last WHERE position to append AND condition
            where_positions = [i for i in range(len(lowered)) if lowered[i:i+7] == ' where ']
            if where_positions:
                last_where = where_positions[-1] + 7
                # Check if there's already a time condition after WHERE
                after_where = lowered[last_where:]
                if 'timestamp' not in after_where:
                    sql += f" AND CAST(timestamp AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {DEFAULT_TIME_INTERVAL_DAYS} DAY)"
        else:
            # No WHERE clause exists, add one
            sql += f" WHERE CAST(timestamp AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {DEFAULT_TIME_INTERVAL_DAYS} DAY)"
    
    # Enforce LIMIT
    if ' limit ' in lowered:
        # clamp existing limit
        import re
        def _clamp(m: re.Match[str]) -> str:
            try:
                val = int(m.group(1))
            except Exception:
                val = MAX_QUERY_ROWS
            return f" LIMIT {min(val, MAX_QUERY_ROWS)}"
        sql = re.sub(r"\slimit\s+(\d+)", lambda m: _clamp(m), sql, flags=re.IGNORECASE)
    else:
        sql += f" LIMIT {MAX_QUERY_ROWS}"
    return sql


# --- Insights helpers ---
def _time_range_to_interval(time_range: str | None) -> str:
    mapping = {
        '1m': 'INTERVAL 30 DAY',
        '3m': 'INTERVAL 90 DAY',
        '6m': 'INTERVAL 180 DAY',
        '1y': 'INTERVAL 365 DAY',
    }
    return mapping.get((time_range or '').lower(), 'INTERVAL 180 DAY')

def _region_filter_sql(region: str | None) -> str:
    r = (region or 'global').lower()
    # Simple coarse bounding boxes
    if r == 'atlantic':
        return "AND lon BETWEEN -70 AND 20"
    if r == 'pacific':
        return "AND (lon >= 120 OR lon <= -70)"
    if r == 'indian':
        return "AND lon BETWEEN 20 AND 120"
    return ""

def _depth_bin_sql(bin_size: int = 50) -> str:
    # pressure approximates depth in meters (1 dbar ≈ 1 m)
    return f"CAST(FLOOR(pressure/{bin_size})*{bin_size} AS INT64)"


@app.post("/insights/temperature", response_model=list[TemperatureDepthPoint])
async def insights_temperature(req: InsightsRequest):
    if bq_client is None:
        raise HTTPException(status_code=503, detail="BigQuery client not ready")
    interval = _time_range_to_interval(req.time_range)
    region_sql = _region_filter_sql(req.region)
    depth_bin = _depth_bin_sql(50)
    sql = f"""
    SELECT {depth_bin} AS depth, AVG(temperature) AS temperature
    FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_NAME}`
    WHERE CAST(timestamp AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), {interval})
    {region_sql}
    AND pressure IS NOT NULL AND temperature IS NOT NULL
    GROUP BY depth
    ORDER BY depth
    """
    df = run_bq_query(sql)
    return df.to_dict(orient='records') if df is not None else []


@app.post("/insights/salinity", response_model=list[SalinityDepthPoint])
async def insights_salinity(req: InsightsRequest):
    if bq_client is None:
        raise HTTPException(status_code=503, detail="BigQuery client not ready")
    interval = _time_range_to_interval(req.time_range)
    region_sql = _region_filter_sql(req.region)
    depth_bin = _depth_bin_sql(50)
    sql = f"""
    SELECT {depth_bin} AS depth, AVG(salinity) AS salinity, AVG(pressure) AS pressure
    FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_NAME}`
    WHERE CAST(timestamp AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), {interval})
    {region_sql}
    AND pressure IS NOT NULL AND salinity IS NOT NULL
    GROUP BY depth
    ORDER BY depth
    """
    df = run_bq_query(sql)
    return df.to_dict(orient='records') if df is not None else []


@app.post("/insights/pressure", response_model=list[PressureDepthPoint])
async def insights_pressure(req: InsightsRequest):
    if bq_client is None:
        raise HTTPException(status_code=503, detail="BigQuery client not ready")
    interval = _time_range_to_interval(req.time_range)
    region_sql = _region_filter_sql(req.region)
    depth_bin = _depth_bin_sql(50)
    sql = f"""
    SELECT {depth_bin} AS depth, AVG(pressure) AS pressure
    FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_NAME}`
    WHERE CAST(timestamp AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), {interval})
    {region_sql}
    AND pressure IS NOT NULL
    GROUP BY depth
    ORDER BY depth
    """
    df = run_bq_query(sql)
    return df.to_dict(orient='records') if df is not None else []

import traceback

from fastapi import Header
import json as _json

# --- FastAPI Events and Endpoints ---

@app.get("/ready", response_model=ReadyResponse)
async def check_readiness():
    """
    Checks if the vector store is ready.
    """
    if is_ready:
        return ReadyResponse(status="ready")
    else:
        raise HTTPException(status_code=503, detail="Server is not ready yet. Please try again in a moment.")

@app.post("/ask", response_model=QueryResponse)
async def ask_question(request: Request, content_type: str = Header(None), stream: bool = False):
    """Main endpoint with conversation context support and optional streaming"""
    
    # Extract session_id and stream parameter FIRST
    session_id = request.query_params.get("session_id")
    stream_mode = request.query_params.get("stream", "").lower() == "true" or stream
    
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())
    
    # Accept JSON, form, or plain text bodies; be lenient with charset
    question = None
    try:
        ct = (content_type or "").lower()
        raw_body = await request.body()
        body_text = raw_body.decode('utf-8', errors='ignore').strip() if raw_body else ""
        # Treat as JSON if header says so OR if it looks like JSON
        looks_like_json = body_text.startswith('{') or body_text.startswith('[')
        if ct.startswith("application/json") or looks_like_json:
            try:
                payload = _json.loads(body_text) if body_text else {}
            except Exception:
                payload = {}
            if isinstance(payload, str):
                question = payload.strip()
            elif isinstance(payload, dict):
                # Accept common alternative keys
                question = (
                    payload.get("question") or
                    payload.get("q") or
                    payload.get("query") or
                    payload.get("message") or
                    payload.get("text") or
                    payload.get("prompt")
                )
                if isinstance(question, str):
                    question = question.strip()
                else:
                    question = None
            else:
                question = None
        elif ct.startswith("application/x-www-form-urlencoded") or ct.startswith("multipart/form-data"):
            form = await request.form()
            question = (
                form.get("question") or
                form.get("q") or
                form.get("query") or
                form.get("message") or
                form.get("text") or
                form.get("prompt") or
                ""
            )
            question = question.strip()
        else:
            # Fallback: treat whole body as the question if non-empty
            if body_text:
                question = body_text
    except Exception:
        question = None

    # Also allow query parameters as a fallback
    if not question:
        qp = request.query_params
        question = (qp.get("question") or qp.get("q") or "").strip()
    
    try:
        if not question:
            help_text = _usage_help()
            if stream_mode:
                return StreamingResponse(
                    stream_response(help_text),
                    media_type="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
                )
            return QueryResponse(answer=help_text, generated_sql="", session_id=session_id)

        print(f"\n{'#'*80}")
        print(f"🔵 NEW QUESTION RECEIVED {'(STREAMING)' if stream_mode else ''}")
        print(f"{'#'*80}")
        print(f"❓ Question: {question}")
        print(f"🔑 Session ID: {session_id}")
        print(f"{'#'*80}\n")

        # Get conversation context
        conversation_context = get_conversation_context(session_id)
        if conversation_context:
            print(f"📚 Conversation Context:")
            print(conversation_context)
            print()

        # Add user question to history
        add_to_conversation_history(session_id, "user", question)

        # Classify intent
        intent = classify_intent(question)
        print(f"🎯 Intent classified as: {intent}\n")

        if intent == "KNOWLEDGE":
            print("📚 Handling as general knowledge question...")
            
            if stream_mode:
                # Get complete response first, then stream character by character
                print("🌊 Starting character-by-character streaming...")
                
                prompt = f"""
    You are Neel Drishti, a friendly and helpful oceanography assistant.
    IMPORTANT: Your name is Neel Drishti. NEVER introduce yourself as OceanIQ or any other name.
    
    Answer clearly and accurately in the user's language.
    Focus on ARGO floats, physical oceanography, and BGC (biogeochemical) parameters when relevant.

    User question:
    {question}

    Requirements:
    - Provide a concise explanation and practical context.
    - If the term is an acronym (e.g., BGC), expand it and list key parameters.
    - Avoid fabricating numeric results from datasets.
    - Use short paragraphs or bullet points with lots of emojis.
    """
                
                async def stream_chars():
                    try:
                        # Get complete response from Cohere (non-streaming)
                        response = cohere_client.chat(
                            model="command-r-plus-08-2024",
                            message=prompt,
                            max_tokens=512,
                            temperature=0.2,
                        )
                        
                        text = response.text if hasattr(response, 'text') else str(response)
                        
                        # Stream character by character with small delay
                        for char in text:
                            yield f"data: {json.dumps({'chunk': char, 'done': False})}\n\n"
                            await asyncio.sleep(0.02)  # 20ms delay between characters
                        
                        yield f"data: {json.dumps({'chunk': '', 'done': True})}\n\n"
                    except Exception as e:
                        print(f"Streaming error: {e}")
                        yield f"data: {json.dumps({'chunk': '', 'done': True, 'error': str(e)})}\n\n"
                
                return StreamingResponse(
                    stream_chars(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "X-Accel-Buffering": "no",
                        "Connection": "keep-alive"
                    }
                )
            else:
                # Get non-streaming response
                summary = answer_general_question(question, stream=False)
                add_to_conversation_history(session_id, "assistant", summary)
                return QueryResponse(answer=summary, generated_sql="", session_id=session_id)

        # DATA intent path with context
        print("📊 Handling as DATA query with context...")
        
        if is_ready and faiss_index is not None and descriptions is not None:
            relevant_profiles = find_relevant_profiles(question)
        else:
            relevant_profiles = []
        
        sql_query = generate_sql_query(question, relevant_profiles, conversation_context)
        
        if stream_mode:
            # Stream character by character for DATA queries
            print(f"🌊 Starting character-by-character streaming for data summary...")
            
            async def stream_data_chars():
                try:
                    # Send immediate "thinking" message
                    thinking_msg = "🔍 Analyzing your ocean data query...\n\n"
                    for char in thinking_msg:
                        yield f"data: {json.dumps({'chunk': char, 'done': False})}\n\n"
                        await asyncio.sleep(0.01)
                    
                    # Run query and build stats
                    results_df = run_bq_query(sql_query)
                    
                    # Build stats
                    stats = {}
                    time_info = ""
                    if results_df is not None and not results_df.empty:
                        if 'time__utc_' in results_df.columns:
                            try:
                                times = pd.to_datetime(results_df['time__utc_'], errors='coerce')
                                if times.notna().any():
                                    tmin = times.min()
                                    tmax = times.max()
                                    time_info = f"from {tmin.strftime('%B %d, %Y')} to {tmax.strftime('%B %d, %Y')}"
                            except Exception:
                                pass
                        
                        if 'temp__degree_celsius_' in results_df.columns:
                            temp = results_df['temp__degree_celsius_'].dropna()
                            if len(temp) > 0:
                                stats['temperature'] = {'min': temp.min(), 'max': temp.max(), 'avg': temp.mean(), 'unit': '°C'}
                        
                        if 'psal__psu_' in results_df.columns:
                            sal = results_df['psal__psu_'].dropna()
                            if len(sal) > 0:
                                stats['salinity'] = {'min': sal.min(), 'max': sal.max(), 'avg': sal.mean(), 'unit': 'PSU'}
                        
                        if 'pres__decibar_' in results_df.columns:
                            pres = results_df['pres__decibar_'].dropna()
                            if len(pres) > 0:
                                stats['pressure'] = {'min': pres.min(), 'max': pres.max(), 'avg': pres.mean(), 'unit': 'dbar'}
                    
                    stats_text = f"Found {len(results_df)} measurements" if results_df is not None else "No data found"
                    if time_info:
                        stats_text += f" {time_info}"
                    for param, data in stats.items():
                        stats_text += f"\n{param.capitalize()}: {data['min']:.2f} to {data['max']:.2f} {data['unit']} (avg: {data['avg']:.2f} {data['unit']})"
                    
                    context_instruction = ""
                    if conversation_context:
                        context_instruction = f"**Previous Conversation:**\n{conversation_context}\n\nUse the conversation history to understand context."
                    
                    prompt = f"""
You are Neel Drishti, a friendly oceanography assistant.
IMPORTANT: Your name is Neel Drishti. NEVER refer to yourself as OceanIQ.
Answer naturally with conversation context.

{context_instruction}

**Current Question:** "{question}"

**Data summary:**
{stats_text}

**Instructions:**
- Write 1-2 natural sentences answering the question
- If this relates to previous questions, acknowledge that connection
- Use specific numbers from the data
- Include units (°C, PSU, dbar)
- Be conversational

Your response:
"""
                    
                    # Get complete response from Cohere (non-streaming)
                    response = cohere_client.chat(
                        model="command-r-plus-08-2024",
                        message=prompt,
                        max_tokens=512,
                        temperature=0.2,
                    )
                    
                    text = response.text if hasattr(response, 'text') else str(response)
                    
                    # Stream character by character with small delay
                    for char in text:
                        yield f"data: {json.dumps({'chunk': char, 'done': False})}\n\n"
                        await asyncio.sleep(0.02)  # 20ms delay between characters
                    
                    yield f"data: {json.dumps({'chunk': '', 'done': True})}\n\n"
                except Exception as e:
                    print(f"Streaming error: {e}")
                    error_msg = f"\n\n❌ Error: {str(e)}"
                    for char in error_msg:
                        yield f"data: {json.dumps({'chunk': char, 'done': False})}\n\n"
                        await asyncio.sleep(0.02)
                    yield f"data: {json.dumps({'chunk': '', 'done': True, 'error': str(e)})}\n\n"
            
            return StreamingResponse(
                stream_data_chars(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                    "Connection": "keep-alive"
                }
            )
        else:
            # Get non-streaming response
            results_df = run_bq_query(sql_query)
            summary = generate_summary(question, results_df, conversation_context, stream=False)
            
            # Add assistant response to history
            add_to_conversation_history(session_id, "assistant", summary)
            
            print(f"✅ Response sent with session: {session_id}\n")
            
            return QueryResponse(answer=summary, generated_sql=sql_query, session_id=session_id)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")
        error_msg = "Sorry, I encountered an error processing your request."
        if stream_mode:
            return StreamingResponse(
                stream_response(error_msg),
                media_type="text/event-stream"
            )
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")


@app.get("/ask", response_model=QueryResponse)
async def ask_question_get(question: str | None = None, q: str | None = None):
    """GET variant for convenience: supports /ask?question=... or /ask?q=..."""
    if not is_ready and not ALLOW_ASK_BEFORE_READY:
        raise HTTPException(status_code=503, detail="Server is not ready yet. Please try again in a moment.")

    text = (question or q or "").strip()
    if not text:
        return QueryResponse(answer=_usage_help(), generated_sql="")

    try:
        # Reuse the same pipeline steps
        if is_ready and faiss_index is not None and descriptions is not None:
            relevant_profiles = find_relevant_profiles(text)
        else:
            relevant_profiles = []

        sql_query = generate_sql_query(text, relevant_profiles)
        results_df = run_bq_query(sql_query)
        summary = generate_summary(text, results_df)
        return QueryResponse(answer=summary, generated_sql=sql_query)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")


@app.post("/analyze")
async def analyze_deprecated():
    """Deprecated endpoint kept to avoid client-side 404 noise."""
    raise HTTPException(status_code=410, detail="/analyze has been removed. Use POST /ask or GET /ask instead.")


@app.get("/ask_with_data", response_model=QueryWithDataResponse)
async def ask_with_data(question: str | None = None, q: str | None = None, session_id: str | None = None, stream: bool = False):
    """Returns both natural-language answer and tabular data for plotting, with optional streaming"""
    if not is_ready and not ALLOW_ASK_BEFORE_READY:
        raise HTTPException(status_code=503, detail="Server is not ready yet.")

    text = (question or q or "").strip()
    stream_mode = stream
    
    if not text:
        raise HTTPException(status_code=400, detail="Provide ?question=... or ?q=...")

    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())

    try:
        print(f"\n{'#'*80}")
        print(f"NEW QUESTION (with data) {'(STREAMING)' if stream_mode else ''}: {text}")
        print(f"{'#'*80}\n")

        # Get conversation context
        conversation_context = get_conversation_context(session_id)
        add_to_conversation_history(session_id, "user", text)

        # RAG context
        if is_ready and faiss_index is not None and descriptions is not None:
            relevant_profiles = find_relevant_profiles(text)
        else:
            relevant_profiles = []

        # Generate and run
        sql_query = generate_sql_query(text, relevant_profiles, conversation_context)
        results_df = run_bq_query(sql_query)
        summary = generate_summary(text, results_df, conversation_context)
        
        add_to_conversation_history(session_id, "assistant", summary)

        # Return serialized rows for plotting
        data_rows = []
        if results_df is not None and not results_df.empty:
            data_rows = results_df.to_dict(orient='records')
            print(f"Returning {len(data_rows)} data rows to frontend")
        
        # Attempt to generate a Plotly chart as PNG (time-series if possible)
        chart_png_b64 = None
        try:
            if results_df is not None and not results_df.empty:
                cols = list(results_df.columns)
                time_col = next((c for c in cols if 'time' in c.lower() or c.endswith('_utc_')), None)
                value_col = None
                for cand in ['temp__degree_celsius_', 'psal__psu_', 'temperature', 'salinity']:
                    if cand in cols:
                        value_col = cand
                        break
                if time_col and value_col:
                    dfp = results_df.copy()
                    dfp[time_col] = pd.to_datetime(dfp[time_col], errors='coerce')
                    dfp = dfp.dropna(subset=[time_col, value_col]).sort_values(time_col)
                    fig = px.line(dfp, x=time_col, y=value_col, title=f"{value_col} over time")
                    fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), template='plotly_dark')
                    img_bytes = fig.to_image(format="png", engine="kaleido", width=800, height=400)
                    chart_png_b64 = base64.b64encode(img_bytes).decode('utf-8')
        except Exception as _e:
            print(f"Plotly render failed: {_e}")

        # If streaming requested, stream the answer but still return full data
        if stream_mode:
            # For streaming with data, we need to return JSON with streaming answer
            # This is complex, so we'll return regular response for now
            # In production, you'd use WebSocket for this use case
            pass
        
        return QueryWithDataResponse(answer=summary, generated_sql=sql_query, data=data_rows, chart_png_b64=chart_png_b64)
        
    except Exception as e:
        print(f"\n{'!'*80}")
        print(f"ERROR in /ask_with_data:")
        print(f"Question: {text if 'text' in locals() else 'N/A'}")
        print(f"Error: {str(e)}")
        print(f"{'!'*80}\n")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")


@app.get("/argo/profiles")
async def list_profiles(limit: int = 50):
    """
    Return a paged list of profile descriptions from the vector store.
    - limit: number of items to return (default 50)
    """
    if not is_ready or faiss_index is None or descriptions is None:
        raise HTTPException(status_code=503, detail="Vector store not ready")
    total = len(descriptions)
    n = max(0, min(limit, total))
    profiles = [{"id": i, "description": descriptions[i]} for i in range(n)]
    return {"count": total, "profiles": profiles}

@app.get("/argo/profiles/{profile_id}")
async def get_profile(profile_id: int):
    """
    Return a single profile description by index id.
    """
    if not is_ready or faiss_index is None or descriptions is None:
        raise HTTPException(status_code=503, detail="Vector store not ready")
    if profile_id < 0 or profile_id >= len(descriptions):
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"id": profile_id, "description": descriptions[profile_id]}

async def stream_response(text: str, delay: float = 0.02):
    """Stream text character by character with explicit flushing for smoother experience"""
    # Stream character by character for smoothest effect
    for char in text:
        yield f"data: {json.dumps({'chunk': char, 'done': False})}\n\n"
        await asyncio.sleep(delay)
    
    # Send completion signal
    yield f"data: {json.dumps({'chunk': '', 'done': True})}\n\n"

async def stream_cohere_response(cohere_stream):
    """Stream Cohere Chat API response token by token in SSE format"""
    try:
        for event in cohere_stream:
            # Cohere streaming events have different types
            if hasattr(event, 'event_type'):
                if event.event_type == 'text-generation':
                    # Extract the text token
                    text_chunk = getattr(event, 'text', '')
                    if text_chunk:
                        yield f"data: {json.dumps({'chunk': text_chunk, 'done': False})}\n\n"
                elif event.event_type == 'stream-end':
                    # Final event
                    yield f"data: {json.dumps({'chunk': '', 'done': True})}\n\n"
            elif hasattr(event, 'text'):
                # Fallback: some SDK versions expose text directly
                text_chunk = event.text
                if text_chunk:
                    yield f"data: {json.dumps({'chunk': text_chunk, 'done': False})}\n\n"
        
        # Ensure we send a completion signal
        yield f"data: {json.dumps({'chunk': '', 'done': True})}\n\n"
    except Exception as e:
        print(f"Streaming error: {e}")
        yield f"data: {json.dumps({'chunk': '', 'done': True, 'error': str(e)})}\n\n"

def get_conversation_context(session_id: str, max_messages: int = 5) -> str:
    """Get recent conversation history as context string"""
    if session_id not in _conversation_history:
        return ""
    
    history = _conversation_history[session_id][-max_messages:]
    context_parts = []
    for msg in history:
        role = "User" if msg["role"] == "user" else "Assistant"
        context_parts.append(f"{role}: {msg['content']}")
    
    return "\n".join(context_parts) if context_parts else ""

def add_to_conversation_history(session_id: str, role: str, content: str):
    """Add a message to conversation history"""
    if session_id not in _conversation_history:
        _conversation_history[session_id] = []
    
    _conversation_history[session_id].append({
        "role": role,
        "content": content,
        "timestamp": pd.Timestamp.now().isoformat()
    })
    
    if len(_conversation_history[session_id]) > MAX_HISTORY_LENGTH:
        _conversation_history[session_id] = _conversation_history[session_id][-MAX_HISTORY_LENGTH:]
