

import google.generativeai as genai
import os

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("GOOGLE_API_KEY environment variable not set.")
genai.configure(api_key=api_key)

for model in genai.list_models():
  if 'generateContent' in model.supported_generation_methods:
    print(model.name)
