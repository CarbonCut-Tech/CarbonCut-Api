import logging
from datetime import datetime
from django.utils import timezone
from ..models import Credential, ProviderType, User

logger = logging.getLogger(__name__)

class GoogleAdsCredentialService:
    @staticmethod
    def save_credential(user: User, tokens: dict, user_info: dict, customer_id: str, customer_data: dict):
        try:
            credential, created = Credential.objects.update_or_create(
                user=user,
                provider=ProviderType.GOOGLE_ADS,
                defaults={
                    'provider_user_id': user_info.get('id', ''),
                    'access_token': tokens['access_token'],
                    'refresh_token': tokens.get('refresh_token'),
                    'expires_at': timezone.now() + timezone.timedelta(hours=1),
                    'extras': {
                        'email': user_info.get('email'),
                        'customer_id': customer_id,
                        'customer_name': customer_data.get('name'),
                        'currency': customer_data.get('currency'),
                        'timezone': customer_data.get('timezone'),
                        'scopes': tokens.get('scopes', []),
                        'authenticated_at': timezone.now().isoformat(),
                    }
                }
            )
            
            action = "created" if created else "updated"
            logger.info(f"Google Ads credential {action} for user: {user.email}")
            
            return credential, None
            
        except Exception as e:
            logger.error(f"Error saving credential: {e}", exc_info=True)
            return None, str(e)
    
    @staticmethod
    def get_credential(user: User):
        try:
            credential = Credential.objects.get(
                user=user,
                provider=ProviderType.GOOGLE_ADS
            )
            return credential, None
        except Credential.DoesNotExist:
            return None, "No Google Ads credential found"
        except Exception as e:
            logger.error(f"Error fetching credential: {e}", exc_info=True)
            return None, str(e)
    
    @staticmethod
    def disconnect_credential(user: User):
        try:
            credential = Credential.objects.get(
                user=user,
                provider=ProviderType.GOOGLE_ADS
            )
            credential.delete()
            logger.info(f"Google Ads credential disconnected for user: {user.email}")
            return True, None
        except Credential.DoesNotExist:
            return False, "No Google Ads credential found"
        except Exception as e:
            logger.error(f"Error disconnecting credential: {e}", exc_info=True)
            return False, str(e)