from django.urls import path
from core.api.controllers.auth import (
    SendOTPView,
    VerifyOTPView,
    GoogleOAuthRedirectView,
    GoogleOAuthCallbackView,
    GoogleAdsStatusView,
    GoogleAdsDisconnectView,
    SignUpView,
    MeView
)

urlpatterns = [
    path('send-otp/', SendOTPView.as_view(), name='auth-send-otp'),
    path('signup/', SignUpView.as_view(), name='auth-signup'),
    path('verify-otp/', VerifyOTPView.as_view(), name='auth-verify-otp'),
    path('me/', MeView.as_view(), name='auth-me'),
    path('google/redirect/', GoogleOAuthRedirectView.as_view(), name='google-oauth-redirect'),
    path('google/callback/', GoogleOAuthCallbackView.as_view(), name='google-oauth-callback'),
    path('google-ads/status/', GoogleAdsStatusView.as_view(), name='google-ads-status'),
    path('google-ads/disconnect/', GoogleAdsDisconnectView.as_view(), name='google-ads-disconnect'),
]