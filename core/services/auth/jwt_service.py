import time
import logging
from typing import Optional, Tuple, Dict, Any
import jwt as pyjwt
from django.conf import settings

logger = logging.getLogger(__name__)

class JWTService:
    ALGORITHM = 'HS256'
    DEFAULT_EXPIRY_DAYS = 30
    
    def create_token(
        self, 
        user_id: str, 
        email: str, 
        expires_in_days: int = DEFAULT_EXPIRY_DAYS
    ) -> str:
        try:
            current_timestamp = int(time.time())
            expiration_timestamp = current_timestamp + (expires_in_days * 24 * 60 * 60)
            payload = {
                'user_id': str(user_id),
                'email': email,
                'iat': current_timestamp,
                'exp': expiration_timestamp,
                'iss': 'carboncut',
                'sub': str(user_id),
                'nbf': current_timestamp
            }
            
            token = pyjwt.encode(
                payload,
                settings.SECRET_KEY,
                algorithm=self.ALGORITHM
            )
            if isinstance(token, bytes):
                token = token.decode('utf-8')
            
            logger.info(f"JWT created for user: {user_id}")
            return token
            
        except Exception as e:
            logger.error(f"Error creating JWT: {e}", exc_info=True)
            raise
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = pyjwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[self.ALGORITHM],
                options={
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_iat': True,
                    'require_exp': True,
                    'require_iat': True
                },
                leeway=10
            )
            
            logger.debug(f"JWT verified for user: {payload.get('user_id')}")
            return payload
            
        except pyjwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except pyjwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying JWT: {e}", exc_info=True)
            return None
    
    def decode_token_from_request(self, request) -> Tuple[Optional[str], Optional[Dict]]:
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        token = None
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            logger.debug("Token from Authorization header")
        else:
            token = request.COOKIES.get('auth-token')
            if token:
                logger.debug("Token from cookie")
        
        if not token:
            logger.debug("No token provided")
            return None, None
        
        payload = self.verify_token(token)
        if not payload:
            return None, None
        
        user_id = payload.get('user_id')
        return user_id, payload