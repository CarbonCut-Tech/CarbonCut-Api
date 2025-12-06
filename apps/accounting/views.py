from django.http import HttpResponse


def index(request):
    return HttpResponse("Accounting module is working")