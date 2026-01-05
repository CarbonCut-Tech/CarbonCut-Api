import logging
from typing import Optional, Tuple, Dict, Any
from datetime import timedelta
from django.utils import timezone
from core.models.user import User, OAuthCredential
from core.db.users import CredentialData

logger = logging.getLogger(__name__)

class OAuthCredentialService:
    def __init__(self):
        self.credential_repo = CredentialData()
    
    def save_google_ads_credential(
        self,
        user: User,
        tokens: Dict[str, Any],
        user_info: Dict[str, Any],
        customer_id: str,
        customer_data: Dict[str, Any]
    ) -> Tuple[Optional[OAuthCredential], Optional[str]]:
        try:
            credential = OAuthCredential(
                id='',  
                user_id=user.id,
                provider='google_ads',
                provider_user_id=user_info.get('id', ''),
                access_token=tokens['access_token'],
                refresh_token=tokens.get('refresh_token'),
                expires_at=timezone.now() + timedelta(hours=1),
                scopes=tokens.get('scopes', []),
                extras={
                    'email': user_info.get('email'),
                    'customer_id': customer_id,
                    'customer_name': customer_data.get('name'),
                    'currency': customer_data.get('currency'),
                    'timezone': customer_data.get('timezone'),
                    'authenticated_at': timezone.now().isoformat(),
                }
            )
            
            saved_credential = self.credential_repo.save(credential)
            
            logger.info(f"Google Ads credential saved for user: {user.email}")
            
            return saved_credential, None
            
        except Exception as e:
            logger.error(f"Error saving credential: {e}", exc_info=True)
            return None, str(e)
    
    def get_credential(
        self, 
        user: User, 
        provider: str = 'google_ads'
    ) -> Tuple[Optional[OAuthCredential], Optional[str]]:
        credential = self.credential_repo.get_by_user_and_provider(user.id, provider)
        
        if not credential:
            return None, f"No {provider} credential found"
        
        return credential, None
    
    def disconnect_credential(
        self, 
        user: User, 
        provider: str = 'google_ads'
    ) -> Tuple[bool, Optional[str]]:
        success = self.credential_repo.delete(user.id, provider)
        
        if success:
            logger.info(f"{provider} credential disconnected for user: {user.email}")
            return True, None
        
        return False, f"No {provider} credential found"