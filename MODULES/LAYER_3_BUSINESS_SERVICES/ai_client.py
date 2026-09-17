import os
from google import genai
from google.genai import types
from MODULES.LAYER_1_CORE_INFRASTRUCTURE.config import GEMINI_API_KEY, MODEL_NAME

client = None

def get_ai_client():
    global client
    if not client:
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            client = genai.Client(api_key=api_key)
    return client

def analyze_attachment(file_bytes, mime_type, context_hint=""):
    try:
        c = get_ai_client()
        if not c:
            return "Could not analyze the attached file (Gemini API not configured)."
        prompt = "Analyze this file in the context of a job interview. " + context_hint + " Be factual and concise, 2-4 sentences only."
        response = c.models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                prompt
            ]
        )
        return response.text.strip()
    except Exception as e:
        print(f"[ATTACHMENT ANALYSIS ERROR] {e}")
        return "Could not analyze the attached file."
