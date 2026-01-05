from typing import Optional, List
from datetime import datetime
from core.models.apikey import APIKey, ConversionRule
import logging

logger = logging.getLogger(__name__)

class APIKeyData:
    def get_by_key(self, key: str) -> Optional[APIKey]:
        from apps.apikey.models import APIKey as DjangoAPIKey
        try:
            orm_key = DjangoAPIKey.objects.get(key=key, is_active=True)
            return self._to_domain(orm_key)
        except DjangoAPIKey.DoesNotExist:
            return None
    
    def get_by_id(self, key_id: str, user_id: str) -> Optional[APIKey]:
        from apps.apikey.models import APIKey as DjangoAPIKey
        
        try:
            orm_key = DjangoAPIKey.objects.get(external_id=key_id, user_id=user_id)
            return self._to_domain(orm_key)
        except DjangoAPIKey.DoesNotExist:
            return None
    
    def get_user_keys(self, user_id: str) -> List[APIKey]:
        from apps.apikey.models import APIKey as DjangoAPIKey
        
        orm_keys = DjangoAPIKey.objects.filter(user_id=user_id).order_by('-created_at')
        return [self._to_domain(k) for k in orm_keys]
    
    def create(self, key: str, name: str, user_id: str, domain: str = '*', industry_category: Optional[str] = None, product: Optional[str] = None) -> APIKey:
        from apps.apikey.models import APIKey as DjangoAPIKey
        
        orm_key = DjangoAPIKey.objects.create(
            key=key,
            name=name,
            user_id=user_id,
            domain=domain,  
            industry_category=industry_category,
            product=product,
            is_active=True
        )
        
        logger.info(f"API key created: {name} for user {user_id}")
        
        return self._to_domain(orm_key)
    
    def save(self, api_key: APIKey) -> APIKey:
        from apps.apikey.models import APIKey as DjangoAPIKey
        
        orm_key = DjangoAPIKey.objects.get(external_id=api_key.id)
        orm_key.name = api_key.name
        orm_key.is_active = api_key.is_active
        orm_key.usage_count = api_key.usage_count
        orm_key.last_used_at = api_key.last_used_at
        orm_key.domain = api_key.domain
        orm_key.save()
        
        return self._to_domain(orm_key)
    
    def delete(self, api_key_id: str, user_id: str) -> bool:
        from apps.apikey.models import APIKey as DjangoAPIKey
        
        try:
            orm_key = DjangoAPIKey.objects.get(external_id=api_key_id, user_id=user_id)
            orm_key.delete()
            logger.info(f"API key deleted: {api_key_id}")
            return True
        except DjangoAPIKey.DoesNotExist:
            return False
    
    def increment_usage(self, api_key: APIKey) -> APIKey:
        from apps.apikey.models import APIKey as DjangoAPIKey
        from django.utils import timezone
        
        orm_key = DjangoAPIKey.objects.get(external_id=api_key.id)
        orm_key.usage_count += 1
        orm_key.last_used_at = timezone.now()  
        orm_key.save(update_fields=['usage_count', 'last_used_at'])
        
        return self._to_domain(orm_key)
    
    def _to_domain(self, orm_key) -> APIKey:
        return APIKey(
            id=str(orm_key.external_id),
            key=orm_key.key,
            name=orm_key.name,
            user_id=orm_key.user_id,
            is_active=orm_key.is_active,
            usage_count=orm_key.usage_count,
            last_used_at=orm_key.last_used_at,
            domain=orm_key.domain,
            industry_category=orm_key.industry_category,
            product=orm_key.product,
            created_at=orm_key.created_at,
            updated_at=orm_key.updated_at
        )


class ConversionRuleData:
    def get_by_id(self, rule_id: str) -> Optional[ConversionRule]:
        from apps.apikey.models import ConversionRule as DjangoConversionRule
        try:
            orm_rule = DjangoConversionRule.objects.get(external_id=rule_id)
            return self._to_domain(orm_rule)
        except DjangoConversionRule.DoesNotExist:
            return None
    
    def get_by_api_key(self, api_key_id: str, active_only: bool = False) -> List[ConversionRule]:
        from apps.apikey.models import ConversionRule as DjangoConversionRule, APIKey as DjangoAPIKey
        try:
            orm_key = DjangoAPIKey.objects.get(external_id=api_key_id)
            queryset = DjangoConversionRule.objects.filter(api_key=orm_key)
            
            if active_only:
                queryset = queryset.filter(is_active=True)
            
            return [self._to_domain(r) for r in queryset.order_by('-priority', '-created_at')]
        except DjangoAPIKey.DoesNotExist:
            return []
    
    def create(self, api_key_id: str, rule_data: dict) -> ConversionRule:
        from apps.apikey.models import ConversionRule as DjangoConversionRule, APIKey as DjangoAPIKey
        
        orm_key = DjangoAPIKey.objects.get(external_id=api_key_id)
        orm_rule = DjangoConversionRule.objects.create(
            api_key=orm_key,
            **rule_data
        )        
        logger.info(f"Conversion rule created: {rule_data.get('name')} for API key {api_key_id}")

        return self._to_domain(orm_rule)
    
    def save(self, rule: ConversionRule) -> ConversionRule:
        from apps.apikey.models import ConversionRule as DjangoConversionRule
        
        orm_rule = DjangoConversionRule.objects.get(external_id=rule.id)
        orm_rule.name = rule.name
        orm_rule.is_active = rule.is_active
        orm_rule.priority = rule.priority
        orm_rule.url_pattern = rule.url_pattern
        orm_rule.match_type = rule.match_type
        orm_rule.css_selector = rule.css_selector
        orm_rule.element_text = rule.element_text
        orm_rule.form_id = rule.form_id
        orm_rule.custom_event_name = rule.custom_event_name
        orm_rule.track_value = rule.track_value
        orm_rule.value_selector = rule.value_selector
        orm_rule.default_value = rule.default_value
        orm_rule.save()
        
        return self._to_domain(orm_rule)

    def delete(self, rule_id: str) -> bool:
        from apps.apikey.models import ConversionRule as DjangoConversionRule
        
        try:
            orm_rule = DjangoConversionRule.objects.get(external_id=rule_id)
            orm_rule.delete()
            logger.info(f"Conversion rule deleted: {rule_id}")
            return True
        except DjangoConversionRule.DoesNotExist:
            return False
    
    def increment_conversion(self, rule: ConversionRule) -> ConversionRule:
        from apps.apikey.models import ConversionRule as DjangoConversionRule
        
        orm_rule = DjangoConversionRule.objects.get(external_id=rule.id)
        orm_rule.conversion_count += 1
        orm_rule.last_triggered_at = datetime.now()
        orm_rule.save(update_fields=['conversion_count', 'last_triggered_at'])
        
        return self._to_domain(orm_rule)
    
    def _to_domain(self, orm_rule) -> ConversionRule:
        return ConversionRule(
            id=str(orm_rule.external_id),
            api_key_id=str(orm_rule.api_key.external_id),
            rule_type=orm_rule.rule_type,
            name=orm_rule.name,
            match_type=orm_rule.match_type,
            url_pattern=orm_rule.url_pattern,
            css_selector=orm_rule.css_selector,
            element_text=orm_rule.element_text,
            form_id=orm_rule.form_id,
            custom_event_name=orm_rule.custom_event_name,
            track_value=orm_rule.track_value,
            value_selector=orm_rule.value_selector,
            default_value=orm_rule.default_value,
            priority=orm_rule.priority,
            is_active=orm_rule.is_active,
            conversion_count=orm_rule.conversion_count,
            last_triggered_at=orm_rule.last_triggered_at,
            created_at=orm_rule.created_at,
            updated_at=orm_rule.updated_at
        )