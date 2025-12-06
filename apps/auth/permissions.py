import logging
from django.conf import settings
import jwt
from rest_framework.permissions import BasePermission
from .models import User

logger = logging.getLogger(__name__)

class IsAuthenticated(BasePermission):
    def has_permission(self, request, view):
        try:
            token = request.COOKIES.get('auth-token')
            if not token:
                auth_header = request.headers.get('Authorization')
                if auth_header and auth_header.startswith('Bearer '):
                    token = auth_header.split(' ')[1]
            
            if not token:
                logger.warning("No token provided")
                return False
            
            decoded = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=["HS256"],
                options={
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_iat': True,
                },
                leeway=10  
            )
            user_id = decoded.get('user_id') 
            
            if not user_id:
                logger.warning("No user_id in token")
                return False

            user = User.objects.filter(id=user_id).first() 

            if user is None:
                logger.warning(f"User not found with id: {user_id}")
                return False
            
            request.user = user
            logger.info(f"User authenticated: {user.email}")
            return True
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return False
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return False
        except Exception as e:
            logger.error(f"Authentication error: {e}", exc_info=True)
            return False






