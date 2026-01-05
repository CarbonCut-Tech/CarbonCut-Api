import logging
import secrets
import hashlib
from typing import List, Optional
from core.models.apikey import APIKey, ConversionRule
from core.db.apikeys import APIKeyData, ConversionRuleData

logger = logging.getLogger(__name__)

class APIKeyService:
    def __init__(self):
        self.api_keys = APIKeyData()
        self.conversion_rules = ConversionRuleData()
    
    def generate_key(self) -> str:
        random_bytes = secrets.token_bytes(32)
        api_key = hashlib.sha256(random_bytes).hexdigest()
        return f"cc_{api_key[:48]}"
    
    def create_api_key(
        self, user_id: str, name: str, domain: str = '*',
        industry_category: Optional[str] = None, product: Optional[str] = None
    ) -> APIKey:
        key = self.generate_key()
        return self.api_keys.create(key, name, user_id, domain, industry_category, product)
    
    def get_user_api_keys(self, user_id: str) -> List[APIKey]:
        return self.api_keys.get_user_keys(user_id)
    
    def get_api_key_by_id(self, key_id: str, user_id: str) -> Optional[APIKey]:
        return self.api_keys.get_by_id(key_id, user_id)
    
    def validate_api_key(self, key: str) -> Optional[APIKey]:
        return self.api_keys.get_by_key(key)
    
    def delete_api_key(self, key_id: str, user_id: str) -> bool:
        return self.api_keys.delete(key_id, user_id)
    
    def toggle_api_key(self, api_key: APIKey) -> APIKey:
        api_key.is_active = not api_key.is_active
        return self.api_keys.save(api_key)
    
    def record_usage(self, api_key: APIKey) -> APIKey:
        return self.api_keys.increment_usage(api_key)


class ConversionRuleService:
    def __init__(self):
        self.rules = ConversionRuleData()
    
    def create_rule(self, api_key_id: str, rule_data: dict) -> ConversionRule:
        return self.rules.create(api_key_id, rule_data)
    
    def get_api_key_rules(self, api_key_id: str, active_only: bool = False) -> List[ConversionRule]:
        return self.rules.get_by_api_key(api_key_id, active_only)
    
    def get_rule_by_id(self, rule_id: str) -> Optional[ConversionRule]:
        return self.rules.get_by_id(rule_id)
    
    def update_rule(self, rule: ConversionRule) -> ConversionRule:
        return self.rules.save(rule)
    
    def delete_rule(self, rule_id: str) -> bool:
        return self.rules.delete(rule_id)
    
    def record_conversion(self, rule: ConversionRule) -> ConversionRule:
        return self.rules.increment_conversion(rule)