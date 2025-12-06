from django.http import HttpResponse
from django.urls import path
from . import views

def index(request):
    return HttpResponse("Events module is working")

urlpatterns = [
    path("", index, name="events-index"),
]
