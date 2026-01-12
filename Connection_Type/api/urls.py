from django.urls import path
from .views import AnalyzePairFromDB, AnalyzeProfile

urlpatterns = [
    # Existing pair analysis by user ids (DB-driven)
    path("analyze-pair/", AnalyzePairFromDB.as_view(), name="analyze-pair-from-db"),

    # New: profile-driven analysis (POST)
    path("profile/analyze/", AnalyzeProfile.as_view(), name="profile-analyze"),
]
