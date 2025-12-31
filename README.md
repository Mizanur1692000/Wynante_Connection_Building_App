Session Gemini Chatbot

A session-based AI chatbot built with Django REST Framework, LangChain, and Google Gemini. Features email-based session management for personalized conversations.

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

API Endpoints

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