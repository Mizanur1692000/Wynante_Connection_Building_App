from django.urls import path
from .views import AnalyzeConnection, ConnectionTypeDistribution, ConnectionTypeDistributionCached, AnalyzePairFromDB

urlpatterns = [
    path("analyze/", AnalyzeConnection.as_view(), name="analyze-connection"),
    path("analyze-pair/", AnalyzePairFromDB.as_view(), name="analyze-pair-from-db"),
    path("analytics/connection-distribution/", ConnectionTypeDistribution.as_view(), name="connection-type-distribution"),
    path("analytics/connection-distribution-cached/", ConnectionTypeDistributionCached.as_view(), name="connection-type-distribution-cached"),
]
