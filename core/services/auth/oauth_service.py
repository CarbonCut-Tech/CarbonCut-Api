import logging
import requests
from typing import Optional, Tuple, Dict, Any
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
    def get_authorization_url(self) -> Tuple[str, str]:
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
                scopes=self.SCOPES,
            )
            
            flow.redirect_uri = redirect_uri
            
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                prompt='consent',
                include_granted_scopes='true',
            )
            
            logger.info(f"OAuth authorization URL generated")
            
            return authorization_url, state
            
        except Exception as e:
            logger.error(f"Error generating authorization URL: {e}", exc_info=True)
            raise
    
    def exchange_code_for_tokens(self, code: str) -> Tuple[Optional[Dict], Optional[str]]:
        try:
            redirect_uri = settings.GOOGLE_OAUTH_REDIRECT_URI.rstrip('/')
            
            flow = Flow.from_client_config(
                client_config={
                    "web": {
                        "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
                        "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/tokenww",
                        "redirect_uris": [redirect_uri],
                    }
                },
                scopes=self.SCOPES,
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
            
            logger.info("Tokens obtained successfully")
            
            return tokens, None
            
        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {e}", exc_info=True)
            return None, str(e)
    def get_user_info(self, access_token: str) -> Tuple[Optional[Dict], Optional[str]]:
        try:
            response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10
            )
            
            if response.status_code != 200:
                return None, f"Failed to get user info: {response.status_code}"
            
            user_info = response.json()
            logger.info("User info retrieved successfully")
            
            return user_info, None
            
        except Exception as e:
            logger.error(f"Error getting user info: {e}", exc_info=True)
            return None, str(e)
    
    def validate_state(
        self, 
        session_state: Optional[str], 
        request_state: str
    ) -> Tuple[bool, Optional[str]]:
        if not session_state:
            return False, "No state in session"
        
        if session_state != request_state:
            return False, "State mismatch"
        
        return True, None