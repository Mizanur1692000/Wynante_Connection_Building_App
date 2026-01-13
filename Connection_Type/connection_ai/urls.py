from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    # Mount both apps at root to match requested endpoints
    path("", include("chatbot.urls")),
    path("", include("api.urls")),
]
