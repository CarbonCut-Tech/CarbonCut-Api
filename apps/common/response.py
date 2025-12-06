from django.http import JsonResponse

def response_factory(data=None, message="", status=200, errors=None):
    return JsonResponse({
        "success": 200 <= status < 300,
        "message": message,
        "data": data,
        "errors": errors,
    }, status=status)