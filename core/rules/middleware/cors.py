from django.http import HttpResponse


class PublicCORSMiddleware:
    PUBLIC_ENDPOINTS = [
        '/api/v1/keys/config',
        '/api/v1/events/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        is_public = any(request.path.startswith(endpoint) for endpoint in self.PUBLIC_ENDPOINTS)
        
        if is_public:
            if request.method == 'OPTIONS':
                response = HttpResponse(status=204)
            else:
                response = self.get_response(request)
            
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = (
                'Content-Type, X-API-Key, X-Tracker-Token, Authorization, '
                'Accept, Accept-Encoding, User-Agent, Referer, Origin, '
                'sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform'
            )
            response['Access-Control-Max-Age'] = '86400'
            response['Access-Control-Allow-Credentials'] = 'false'
            
            return response
        
        return self.get_response(request)