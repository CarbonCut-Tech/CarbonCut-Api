from django.urls import path
from core.api.controllers.apikey import (
    APIKeyView,
    APIKeyDetailView,
)
from core.api.controllers.apikey_config import APIKeyConfigView

urlpatterns = [
    path('config', APIKeyConfigView.as_view(), name='apikey-config'),
    path('', APIKeyView.as_view(), name='apikey-list-create'),
    path('<str:key_id>/', APIKeyDetailView.as_view(), name='apikey-detail'),
    path('<str:key_id>/toggle/', APIKeyDetailView.as_view(), name='apikey-toggle'),
]