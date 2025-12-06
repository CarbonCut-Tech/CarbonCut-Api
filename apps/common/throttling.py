from rest_framework.throttling import SimpleRateThrottle

class CustomUserRateThrottle(SimpleRateThrottle):
    scope = 'user'

    def get_cache_key(self, request, view):
        if hasattr(request, 'user') and request.user and hasattr(request, 'user') and request.user.id:
            ident = request.user.id
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class CustomAnonRateThrottle(SimpleRateThrottle):
    scope = 'anon'

    def get_cache_key(self, request, view):
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'id') and request.user.id:
            return None  
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request)
        }


class ExcludeEventsThrottle(SimpleRateThrottle):
    scope = 'default'

    def allow_request(self, request, view):
        if request.resolver_match and request.resolver_match.app_name == 'event':
            return True
        
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'id') and request.user.id:
            ident = request.user.id
        else:
            ident = self.get_ident(request)

        self.key = self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }
        
        return super().allow_request(request, view)