from django.urls import path
from .views import CampaignView, CampaignDetailView

urlpatterns = [
    path('', CampaignView.as_view(), name='campaigns'),
    path('<str:campaign_id>/', CampaignDetailView.as_view(), name='campaign-detail'),
]
