import logging
from django.http import JsonResponse
from django.conf import settings
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CookieService:

    @staticmethod
    def set_auth_cookie(response, token: str, max_age: int = 60*60*24*30):
        is_production = not settings.DEBUG
        expires = datetime.utcnow() + timedelta(seconds=max_age)
        expires_str = expires.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        cookie_parts = [
            f'auth-token={token}',
            f'Max-Age={max_age}',
            f'Expires={expires_str}',
            'Path=/',
        ]

        if is_production:
            cookie_parts.append('Secure')
            cookie_parts.append('SameSite=None')
            logger.info(f"   Secure: TRUE (HTTPS required)")
            logger.info(f"   SameSite: None (cross-domain)")
        else:
            cookie_parts.append('SameSite=Lax')
            logger.info(f"   Secure: FALSE (HTTP allowed)")
            logger.info(f"   SameSite: Lax (local dev)")
        
        cookie_value = '; '.join(cookie_parts)

        response['Set-Cookie'] = cookie_value
        
        logger.info(f"   Complete Set-Cookie header:")
        
        logger.info(f"   Response type: {type(response).__name__}")

        if hasattr(response, 'headers'):
            logger.info(f"   Response headers count: {len(response.headers)}")
        
        logger.info("Cookie set successfully")
        logger.info("=" * 80)
        
        return response
    
    @staticmethod
    def delete_auth_cookie(response):
        is_production = not settings.DEBUG
        
        cookie_parts = [
            'auth-token=',
            'Max-Age=0',
            'Expires=Thu, 01 Jan 1970 00:00:00 GMT',
            'Path=/',
        ]
        
        if is_production:
            cookie_parts.append('Secure')
            cookie_parts.append('SameSite=None')
            logger.info(f"   Secure: TRUE")
            logger.info(f"   SameSite: None")
        else:
            cookie_parts.append('SameSite=Lax')
            logger.info(f"   Secure: FALSE")
            logger.info(f"   SameSite: Lax")
        
        cookie_value = '; '.join(cookie_parts)
        response['Set-Cookie'] = cookie_value
        
        logger.info(f"   Complete Set-Cookie header:")
        logger.info(f"   {cookie_value}")
        logger.info("    Cookie deleted successfully")
        
        return response