Unified Wynante Project

Overview
This project now combines the original Chatbot and Connection Type functionalities into a single Django project that exposes four endpoints:

- chat/ — Chat with Anchor AI (POST)
- set_email/ — Initialize session by setting email (POST)
- analyze-pair/ — Analyze a pair by user IDs (GET)
- profile/analyze/ — Analyze a profile + recent posts/comments (POST)

Environment
Create `.env` and set values (local example):

```
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
GEMINI_API_KEY=your-gemini-api-key
# Optionally for production
# DATABASE_URL=postgres://user:pass@host:5432/dbname
# SECURE_SSL_REDIRECT=True
# SECURE_HSTS_SECONDS=3600
```

Install
```
pip install -r requirements.txt
```

Migrate
```
cd Connection_Type
python manage.py migrate
```

Run (Dev)
```
python manage.py runserver 127.0.0.1:8000
```

Run (Production ASGI)
```
uvicorn connection_ai.asgi:application --host 0.0.0.0 --port 8000 --workers 4
```

Endpoints (session_id required after set_email)
- POST /set_email/ {"email": "user@example.com"}
- POST /chat/ {"message": "Hello", "session_id": "<from set_email>"}
- GET /analyze-pair/?user_a_id=1&user_b_id=2&session_id=<from set_email>
- POST /profile/analyze/ {"session_id": "<from set_email>", profile fields...}

Notes
- `session_id` is mandatory for all endpoints except `set_email/`.
- If `GEMINI_API_KEY` is missing or the LLM fails, chat may not work; profile analysis falls back to heuristics.
