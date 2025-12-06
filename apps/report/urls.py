from django.http import HttpResponse
from django.urls import path
from . import views

def index(request):
    return HttpResponse("Reports module is working")

urlpatterns = [
    path("", index, name="reports-index"),
]
