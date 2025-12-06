from .views import (
    LogoutUserView, UserDetailView, SendOTPView, VerifyOTPView,
    GoogleOAuthRedirectView, GoogleOAuthCallbackView,
    GoogleAdsStatusView, GoogleAdsDisconnectView
)
from django.urls import path

urlpatterns = [
    path("verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("send-otp/", SendOTPView.as_view(), name="send-otp"),
    path("logout/", LogoutUserView.as_view(), name="logout-user"),
    path("me/", UserDetailView.as_view(), name="auth-user-detail"),
    
    path("google/redirect/", GoogleOAuthRedirectView.as_view(), name="google-oauth-redirect"),
    path("google/callback/", GoogleOAuthCallbackView.as_view(), name="google-oauth-callback"),
    path("google-ads/status/", GoogleAdsStatusView.as_view(), name="google-ads-status"),
    path("google-ads/disconnect/", GoogleAdsDisconnectView.as_view(), name="google-ads-disconnect"),
]