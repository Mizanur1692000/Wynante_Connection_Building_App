from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
from .serializers import ChatRequestSerializer, ChatResponseSerializer, EmailSerializer
from django.conf import settings
from django.contrib.sessions.models import Session
import uuid
import re

class EmailView(CreateAPIView):
    serializer_class = EmailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        # Generate unique session ID based on email
        session_id = f"{email}_{uuid.uuid4().hex[:8]}"
        
        # Create a new session
        request.session.create()
        
        # Store email and our custom session ID
        request.session['user_email'] = email
        request.session['custom_session_id'] = session_id
        
        return Response({
            "message": f"Email set successfully: {email}. You can now use the chatbot.",
            "session_id": session_id
        }, status=status.HTTP_200_OK)

class ChatView(CreateAPIView):
    serializer_class = ChatRequestSerializer

    def get_session_by_custom_id(self, session_id):
        """Find session by our custom session ID"""
        sessions = Session.objects.all()
        for session in sessions:
            session_data = session.get_decoded()
            if session_data.get('custom_session_id') == session_id:
                return session, session_data
        return None, None

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_message = serializer.validated_data['message']
        session_id = serializer.validated_data['session_id']
        
        if not session_id:
            raise ValidationError("Session ID is required")
        
        # Find session by custom session ID
        session_obj, session_data = self.get_session_by_custom_id(session_id)
        
        if not session_obj or not session_data:
            raise NotFound("Invalid session ID. Please set your email first via /set_email/")
        
        if 'user_email' not in session_data:
            raise NotFound("Invalid session. Please set your email first via /set_email/")
        
        # Chat processing logic
        chat_history_key = f'chat_history_{session_id}'
        chat_history = ChatMessageHistory()
        
        # Load history
        history_data = session_data.get(chat_history_key, [])
        for item in history_data:
            if item['type'] == 'human':
                chat_history.add_user_message(item['content'])
            elif item['type'] == 'ai':
                chat_history.add_ai_message(item['content'])
        
        # Set up LLM for connection-building
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.7,
        )
        
        # Update prompt to instruct the AI to act as a connection-building companion
        prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        (
            "You are Anchor AI, a focused companion for an intelligent connection-building platform. "
            "Your role is to support intentional, healthy relationships, meaningful conversations, "
            "community engagement, professional networking, and personal growth within this platform.\n\n"

            "WHAT YOU HELP WITH:\n"
            "- Clarifying values, goals, boundaries, and communication styles\n"
            "- Guiding focused connection sessions and relationship check-ins\n"
            "- Encouraging respectful community interaction\n"
            "- Supporting career-related conversations and collaboration\n"
            "- Promoting reflective or spiritual habits in an inclusive way\n\n"

            "HOW YOU RESPOND:\n"
            "- Be warm, calm, and respectful\n"
            "- Use clear, structured, and actionable guidance\n"
            "- Avoid judgment and avoid abstract advice\n"
            "- Output must be plain text sentences with no markdown, no asterisks (*), no emojis, and no decorative symbols.\n\n"

            "STRICT SCOPE RULE (MANDATORY):\n"
            "- You are NOT a general-purpose assistant\n"
            "- Do NOT provide external information, factual knowledge, news, definitions, "
            "technical explanations, or unrelated advice\n\n"

            "IF A REQUEST IS OUT OF SCOPE:\n"
            "Respond ONLY with this message:\n"
            "\"I am Anchor AI, a focused companion for an intelligent connection-building platform. I am here specifically to support connection-building, relationships, and personal or "
            "professional growth within this platform. I am unable to help with that topic, but I can "
            "support you with reflection, communication, or next steps within a connection if you’d like.\""
        ),
    ),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])
        
        chain = prompt | llm
        
        runnable_with_history = RunnableWithMessageHistory(
            chain,
            lambda session_id: chat_history,
            input_messages_key="input",
            history_messages_key="history",
        )
        
        config = {"configurable": {"session_id": session_id}}
        response = runnable_with_history.invoke({"input": user_message}, config=config)
        ai_response = response.content

        # Sanitize response: remove asterisks, backticks, bullets, emojis/symbols; collapse whitespace
        def _sanitize_response(text: str) -> str:
            if not isinstance(text, str):
                return text
            # Remove specific markup characters
            text = text.replace("*", "").replace("`", "").replace("•", "")
            # Remove common emoji/symbol ranges
            emoji_pattern = re.compile(
                "[" 
                u"\U0001F600-\U0001F64F"  # emoticons
                u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                u"\U0001F680-\U0001F6FF"  # transport & map symbols
                u"\U0001F700-\U0001F77F"  # alchemical symbols
                u"\U0001F780-\U0001F7FF"  # geometric shapes extended
                u"\U0001F800-\U0001F8FF"  # supplemental arrows-c
                u"\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
                u"\U0001FA00-\U0001FA6F"  # chess symbols
                u"\U0001FA70-\U0001FAFF"  # symbols & pictographs extended-a
                u"\U00002700-\U000027BF"  # dingbats
                u"\U00002600-\U000026FF"  # misc symbols
                u"\U00002B00-\U00002BFF"  # arrows & misc
                u"\U0000FE00-\U0000FE0F"  # variation selectors
                u"\U000024C2-\U0001F251"  # enclosed characters
                "]",
                flags=re.UNICODE,
            )
            text = emoji_pattern.sub("", text)
            # Collapse whitespace to single spaces
            text = re.sub(r"\s+", " ", text).strip()
            return text

        ai_response = _sanitize_response(ai_response)
        
        # Save updated history
        history_data = []
        for msg in chat_history.messages:
            if isinstance(msg, HumanMessage):
                history_data.append({'type': 'human', 'content': msg.content})
            elif isinstance(msg, AIMessage):
                history_data.append({'type': 'ai', 'content': msg.content})
        
        # Update session
        session_data[chat_history_key] = history_data
        session_obj.session_data = Session.objects.encode(session_data)
        session_obj.save()
        
        response_serializer = ChatResponseSerializer({'response': ai_response})
        return Response(response_serializer.data, status=status.HTTP_200_OK)
