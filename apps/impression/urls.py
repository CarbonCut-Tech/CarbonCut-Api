from apps.auth.views import GoogleAdsStatusView, GoogleOAuthRedirectView,GoogleOAuthCallbackView as GoogleCallbackApiView
from django.http import HttpResponse
from django.urls import path

def index(request):
    return HttpResponse("Impressions module is working")

urlpatterns = [
    path("", index, name="impressions-index"),
    path('google/redirect/', GoogleOAuthRedirectView.as_view(), name='google_oauth_redirect'),  # ✅ Add this
    path('google/callback/', GoogleCallbackApiView.as_view(), name='google_callback'),
    path('google-ads/status/', GoogleAdsStatusView.as_view(), name='google_ads_status'),
]
