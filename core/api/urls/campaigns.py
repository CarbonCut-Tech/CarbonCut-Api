from django.urls import path
from core.api.controllers.campaigns import (
    CampaignListCreateView,
    CampaignDetailView,
    CampaignAnalyticsView,
    SyncCampaignView,
)

urlpatterns = [
    path('', CampaignListCreateView.as_view(), name='campaign-list-create'),
    path('<str:external_id>/', CampaignDetailView.as_view(), name='campaign-detail'),
    
    path('<str:external_id>/analytics/', CampaignAnalyticsView.as_view(), name='campaign-analytics'),

    path('<str:external_id>/sync/', SyncCampaignView.as_view(), name='campaign-sync'),
]