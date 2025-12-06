from django.http import HttpResponse
from django.urls import path
from . import views

def index(request):
    return HttpResponse("Projects module is working")

urlpatterns = [
    path("", index, name="projects-index"),
]
