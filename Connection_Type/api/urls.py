from django.urls import path
from .views import AnalyzePairFromDB

urlpatterns = [
    path("analyze-pair/", AnalyzePairFromDB.as_view(), name="analyze-pair-from-db"),
]
