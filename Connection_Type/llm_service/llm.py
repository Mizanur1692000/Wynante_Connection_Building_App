import os
import json
from typing import Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

_api_key = os.getenv("GEMINI_API_KEY")
_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
llm: Optional[ChatGoogleGenerativeAI] = None
if _api_key:
    llm = ChatGoogleGenerativeAI(
        model=_model,
        google_api_key=_api_key,
        temperature=0.0
    )

PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a careful analyzer. Base decisions only on the "
        "provided conversation content. Avoid hallucination. Return "
        "deterministic structured JSON with feature values between 0 and 1."
    )),
    ("user", (
        "Analyze the following two-person conversation and return STRICT JSON "
        "with keys: emotional_warmth, emotional_intensity, formality, task_focus, "
        "romantic_language, spiritual_reference. Values must be floats between 0 and 1.\n\n"
        "Conversation:\n{conversation}"
    )),
])

def extract_features(messages: list) -> dict:
    conversation_text = "\n".join(
        f"{m['sender']}: {m['text']}" for m in messages
    )

    # If LLM is not initialized (missing key), return empty and rely on heuristic fallback
    if llm is None:
        return {}

    chain = PROMPT | llm
    # Basic retry with small attempt count to avoid transient failures
    attempt = 0
    response_text = None
    while attempt < 2 and response_text is None:
        try:
            response = chain.invoke({"conversation": conversation_text})
            response_text = response.content
        except Exception:
            attempt += 1
            response_text = None
            continue

    # Parse STRICT JSON from the LLM safely
    try:
        data = json.loads(response_text) if response_text else {}
    except json.JSONDecodeError:
        data = {}

    # Ensure required keys exist with defaults
    required_keys = [
        "emotional_warmth",
        "emotional_intensity",
        "formality",
        "task_focus",
        "romantic_language",
        "spiritual_reference",
    ]
    for key in required_keys:
        data.setdefault(key, 0.0)

    return data
