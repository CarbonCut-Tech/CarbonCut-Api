import logging
import secrets
import hashlib
from typing import List, Optional
from django.db import models
from django.db.models import Count
from ..models import APIKey
from apps.auth.models import User

logger = logging.getLogger(__name__)

class APIKeyService:
    @staticmethod
    def generate_api_key() -> str:
        random_bytes = secrets.token_bytes(32)
        api_key = hashlib.sha256(random_bytes).hexdigest()
        return f"cc_{api_key[:48]}"

    @staticmethod
    def create_api_key(user: User, name: str, domain: str = '*') -> APIKey:
        key = APIKeyService.generate_api_key()
        
        api_key = APIKey.objects.create(
            key=key,
            name=name,
            user_id=str(user.id),
            domain=domain,
            is_active=True
        )
        
        logger.info(f"API key created: {name} for user {user.id}")
        return api_key

    @staticmethod
    def get_user_api_keys(user: User) -> List[APIKey]:
        return APIKey.objects.filter(user_id=str(user.id)).annotate(
            conversion_rules_count=Count('conversion_rules', filter=models.Q(conversion_rules__is_active=True))
        ).order_by('-created_at')

    @staticmethod
    def get_api_key_by_id(key_id: str, user: User) -> Optional[APIKey]:
        return APIKey.objects.filter(external_id=key_id, user_id=str(user.id)).first()

    @staticmethod
    def validate_api_key(key: str) -> Optional[APIKey]:
        return APIKey.objects.filter(key=key, is_active=True).first()

    @staticmethod
    def delete_api_key(api_key: APIKey) -> None:
        logger.info(f"Deleting API key: {api_key.name}")
        api_key.delete()

    @staticmethod
    def toggle_api_key(api_key: APIKey) -> APIKey:
        api_key.is_active = not api_key.is_active
        api_key.save(update_fields=['is_active', 'updated_at'])
        logger.info(f"API key {api_key.name} {'activated' if api_key.is_active else 'deactivated'}")
        return api_key