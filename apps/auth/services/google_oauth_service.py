import logging
import requests
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

class GoogleOAuthService:
    SCOPES = [
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
        'openid',
        'https://www.googleapis.com/auth/adwords',
    ]
    
    @staticmethod
    def get_authorization_url():
        try:
            redirect_uri = settings.GOOGLE_OAUTH_REDIRECT_URI.rstrip('/')
            
            flow = Flow.from_client_config(
                client_config={
                    "web": {
                        "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
                        "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [redirect_uri],
                    }
                },
                scopes=GoogleOAuthService.SCOPES,
            )
            
            flow.redirect_uri = redirect_uri
            
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                prompt='consent',
                include_granted_scopes='true',
            )
            
            logger.info(f"OAuth authorization URL generated with state: {state}")
            
            return authorization_url, state
            
        except Exception as e:
            logger.error(f"Error generating authorization URL: {e}", exc_info=True)
            raise
    
    @staticmethod
    def exchange_code_for_tokens(code: str):
        try:
            redirect_uri = settings.GOOGLE_OAUTH_REDIRECT_URI.rstrip('/')
            
            flow = Flow.from_client_config(
                client_config={
                    "web": {
                        "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
                        "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [redirect_uri],
                    }
                },
                scopes=GoogleOAuthService.SCOPES,
            )
            
            flow.redirect_uri = redirect_uri
            flow.fetch_token(code=code)
            
            credentials = flow.credentials
            
            tokens = {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes,
                'expires_at': (timezone.now() + timedelta(hours=1)).isoformat(),
            }
            
            logger.info(f"Tokens obtained successfully")
            
            return tokens, None
            
        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {e}", exc_info=True)
            return None, str(e)
    
    @staticmethod
    def get_user_info(access_token: str):
        try:
            response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10
            )
            
            response.raise_for_status()
            user_info = response.json()
            
            logger.info(f"User info retrieved: {user_info.get('email')}")
            
            return user_info, None
            
        except Exception as e:
            logger.error(f"Error getting user info: {e}", exc_info=True)
            return None, str(e)
    
    @staticmethod
    def validate_state(session_state: str, callback_state: str):
        if not session_state:
            return False, "No session state found"
        
        if session_state != callback_state:
            return False, "State mismatch - possible CSRF attack"
        
        return True, None