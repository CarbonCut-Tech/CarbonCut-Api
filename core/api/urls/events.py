from django.urls import path
from core.api.controllers.events import (
    EventCollectorView,
    SupportedEventsView
)

urlpatterns = [
    path('', EventCollectorView.as_view(), name='event-collect'),
    path('supported/', SupportedEventsView.as_view(), name='event-supported'),
]