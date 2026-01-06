from django.urls import path, include

urlpatterns = [
    path('', include('core.api.urls.emission_sources')),  
    path('apikeys/', include('core.api.urls.apikeys')),
    path('auth/', include('core.api.urls.auth')),
    path('events/', include('core.api.urls.events')),
    path('campaigns/', include('core.api.urls.campaigns')),
]