from django.urls import path
from .views import AnalyzeConnection

urlpatterns = [
    path("analyze/", AnalyzeConnection.as_view(), name="analyze-connection")
]
