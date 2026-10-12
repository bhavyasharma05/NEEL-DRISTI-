import os
import requests
import pandas as pd
import streamlit as st
import plotly.express as px

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Neel Drishti Charts", layout="wide")
st.title("Neel Drishti AI – Interactive Charts")

with st.sidebar:
    st.header("Settings")
    backend = st.text_input("Backend URL", value=BACKEND_URL)
    st.caption("Example: http://localhost:8000")

st.write("Ask for trends or comparisons, e.g., 'show temperature trend 2023', 'salinity near 10N,60W last month'.")

question = st.text_input("Your question", value="show temperature trend 2023")

col1, col2 = st.columns([1, 3])
with col1:
    if st.button("Analyze"):
        if not question.strip():
            st.warning("Please enter a question.")
        else:
            try:
                with st.spinner("Querying backend..."):
                    resp = requests.get(f"{backend}/ask_with_data", params={"question": question}, timeout=60)
                if resp.status_code != 200:
                    st.error(f"Backend error {resp.status_code}: {resp.text}")
                else:
                    payload = resp.json()
                    st.subheader("Answer")
                    st.write(payload.get("answer") or "No answer.")

                    rows = payload.get("data") or []
                    if not rows:
                        st.info("No tabular data returned for plotting.")
                    else:
                        df = pd.DataFrame(rows)
                        st.subheader("Data Preview")
                        st.dataframe(df.head(200), use_container_width=True)

                        # Heuristics to pick time and value columns
                        time_candidates = [c for c in df.columns if "time" in c.lower() or c.endswith("_utc_")]
                        value_candidates = [
                            c for c in df.columns
                            if any(k in c.lower() for k in ["temp", "temperature", "psal", "salinity", "value"]) and pd.api.types.is_numeric_dtype(df[c])
                        ]

                        time_col = time_candidates[0] if time_candidates else None
                        value_col = value_candidates[0] if value_candidates else None

                        if time_col and value_col:
                            # Try to parse datetime
                            df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
                            df_plot = df.dropna(subset=[time_col, value_col]).sort_values(by=time_col)
                            fig = px.line(df_plot, x=time_col, y=value_col, title=f"{value_col} over time")
                            st.plotly_chart(fig, use_container_width=True)
                        elif value_candidates:
                            fig = px.histogram(df, x=value_candidates[0], nbins=40, title=f"Distribution of {value_candidates[0]}")
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("Could not detect suitable columns for plotting. Download the data to explore more.")

                        st.download_button(
                            label="Download CSV",
                            data=df.to_csv(index=False).encode('utf-8'),
                            file_name="neel_drishti_results.csv",
                            mime="text/csv",
                        )
            except Exception as e:
                st.exception(e)

with col2:
    st.empty()
