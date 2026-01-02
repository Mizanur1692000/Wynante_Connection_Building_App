import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.2
)

PROMPT = ChatPromptTemplate.from_template("""
Analyze the following conversation.

Return STRICT JSON with values between 0 and 1:
- emotional_warmth
- emotional_intensity
- formality
- task_focus
- romantic_language
- spiritual_reference

Conversation:
{conversation}
""")

def extract_features(messages: list) -> dict:
    conversation_text = "\n".join(
        f"{m['sender']}: {m['text']}" for m in messages
    )

    chain = PROMPT | llm
    response = chain.invoke({"conversation": conversation_text})

    # Parse STRICT JSON from the LLM safely
    try:
        data = json.loads(response.content)
    except json.JSONDecodeError:
        # Fallback to zeros if parsing fails
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
