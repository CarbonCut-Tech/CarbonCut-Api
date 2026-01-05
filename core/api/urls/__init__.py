from django.urls import path, include

urlpatterns = [
    path('auth/', include('core.api.urls.auth')),
    path('keys/', include('core.api.urls.apikeys')),
    path('events/', include('core.api.urls.events')),
    path('campaigns/', include('core.api.urls.campaigns')),  
]