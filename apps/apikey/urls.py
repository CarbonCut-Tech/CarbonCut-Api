from django.urls import path
from .views import (
    APIKeyView,
    APIKeyDetailView,
    ConversionRulesView,
    ConversionRuleDetailView,
    APIKeyVerificationView,
    APIKeyInstallationGuideView,
    get_conversion_config
)

urlpatterns = [
    path('', APIKeyView.as_view(), name='api-keys'),
    path('<str:key_id>/', APIKeyDetailView.as_view(), name='api-key-detail'),
    path('<str:key_id>/toggle/', APIKeyDetailView.as_view(), name='api-key-toggle'),
    
    path('<str:key_id>/rules/', ConversionRulesView.as_view(), name='conversion-rules'),
    path('<str:key_id>/rules/<str:rule_id>/', ConversionRuleDetailView.as_view(), name='conversion-rule-detail'),
    path('<str:key_id>/verify/', APIKeyVerificationView.as_view(), name='verify-installation'),
    path('<str:key_id>/installation/', APIKeyInstallationGuideView.as_view(), name='installation-guide'),
    
    path('config/conversion-rules/', get_conversion_config, name='conversion-config'),
]
