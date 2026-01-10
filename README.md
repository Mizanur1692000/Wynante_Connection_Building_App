Wynante Connection_Type API (Production-ready)

Overview
This is a production-ready, AI-driven two-person conversation analyzer. It exposes a single endpoint that reads conversations from the database and returns independent 0–100 scores for Social, Romantic, Spiritual, Professional, plus the highest type.

Environment
Copy `.env.example` to `.env` and set values:

```
SECRET_KEY=change-me
DEBUG=False
ALLOWED_HOSTS=your.domain.com
DATABASE_URL=postgres://user:pass@host:5432/dbname
GEMINI_API_KEY=your-gemini-api-key
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=3600
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
Use uvicorn (or gunicorn+daphne) with the ASGI app:
```
uvicorn connection_ai.asgi:application --host 0.0.0.0 --port 8000 --workers 4
```

Endpoint
- GET /api/analyze-pair/?user_a_id=1&user_b_id=2

Notes
- If `GEMINI_API_KEY` is missing or the LLM fails, the system falls back to heuristics.
- Only the required endpoint is exposed; analytics/testing endpoints were removed.