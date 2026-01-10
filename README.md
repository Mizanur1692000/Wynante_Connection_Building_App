Session Gemini Chatbot + Connection Type API

A workspace with two Django REST projects:
- Chatbot: Session-based AI chatbot using LangChain + Google Gemini.
- Connection_Type: API that analyzes a conversation and classifies connection type.

Features

Email-based session authentication

AI-powered conversations using Google Gemini

Conversation history per session

RESTful API architecture

LangChain integration for AI workflows

Tech Stack

Backend: Django REST Framework

AI: Google Gemini, LangChain

Session Management: Django Sessions

API: RESTful endpoints

Chatbot API Endpoints

Set Email & Create Session
POST /api/set_email/
{
"email": "user@example.com"
}

Chat with AI
POST /api/chat/
{
"message": "Hello, how are you?",
"session_id": "your_session_id"
}

Setup

Clone the repository

Install dependencies: pip install -r requirements.txt

Set up environment variables:
GEMINI_API_KEY=your_gemini_api_key

Run migrations: python manage.py migrate

Start server: python manage.py runserver

Usage

First, set your email to create a session

Use the returned session_id for all chat requests

Each session maintains its own conversation history

Quick Try (Windows PowerShell)

Set Email & Get Session ID

curl -X POST http://127.0.0.1:8000/api/set_email/ -H "Content-Type: application/json" -d '{"email":"user@example.com"}'

Chat with AI (Math-only)

curl -X POST http://127.0.0.1:8000/api/chat/ -H "Content-Type: application/json" -d '{"message":"What is 12*8?","session_id":"<paste_session_id_here>"}'

Notes
- Uses `langchain-google-genai` with the supported `google.genai` SDK.
- Configure `GEMINI_API_KEY` in your `.env`.

Connection_Type Project

Setup (Windows PowerShell)

1. Create/activate venv and install requirements (already handled if using workspace venv).
2. Run migrations and start the server.

Commands

```
cd Connection_Type
..\venv\Scripts\python.exe manage.py makemigrations api
..\venv\Scripts\python.exe manage.py migrate
..\venv\Scripts\python.exe manage.py runserver
```

Environment
- Optional: `DATABASE_URL` for Postgres via `dj-database-url`.
- If using Postgres, `psycopg2-binary` is installed.

Endpoints
- POST /api/analyze/

Request body
```
{
	"messages": [
		{"sender": "Alice", "text": "Hi! How are you?"},
		{"sender": "Bob", "text": "Let's schedule a meeting for the project."}
	]
}
```

Example (PowerShell)
```
$body = @{ messages = @(@{ sender = "Alice"; text = "Hi!" }, @{ sender = "Bob"; text = "Work updates" }) } | ConvertTo-Json -Depth 4
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/analyze/" -ContentType "application/json" -Body $body
```

Notes
- LLM features are parsed as JSON safely; missing keys default to 0.
- Classification logic applies simple profile similarity and rule overrides.