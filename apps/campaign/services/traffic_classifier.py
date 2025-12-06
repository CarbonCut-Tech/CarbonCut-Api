import logging
from typing import Dict, Optional
from django.core.cache import cache
from urllib.parse import urlparse
from ..models import TrafficClassificationRule, Campaign

logger = logging.getLogger(__name__)


class TrafficClassifier:
    @staticmethod
    def classify_session(
        utm_params: Dict[str, str],
        referrer: str = '',
        campaign: Optional[Campaign] = None
    ) -> str:
        if campaign and (campaign.google_ads_campaign_id or campaign.google_ads_customer_id):
            return 'paid_ads'
        
        utm_source = utm_params.get('utm_source', '').lower()
        utm_medium = utm_params.get('utm_medium', '').lower()
        utm_campaign = utm_params.get('utm_campaign', '').lower()
        
        paid_mediums = ['cpc', 'ppc', 'paid', 'paidsearch', 'display', 'retargeting']
        if utm_medium in paid_mediums:
            return 'paid_ads'
        
        paid_sources = ['google', 'facebook', 'linkedin', 'twitter', 'instagram']
        if utm_source in paid_sources and utm_campaign:
            return 'paid_ads'
        
        rules = TrafficClassificationRule.objects.filter(is_active=True).order_by('-priority')
        
        for rule in rules:
            if TrafficClassifier._matches_rule(rule, utm_params, referrer):
                return rule.traffic_type
        
        if utm_source == 'email' or utm_medium == 'email':
            return 'email'
        
        if utm_source in ['facebook', 'twitter', 'linkedin', 'instagram'] and not utm_medium:
            return 'social'
        
        if referrer:
            domain = urlparse(referrer).netloc
            if domain and domain != '':
                return 'organic'
        
        return 'direct'
    
    @staticmethod
    def _matches_rule(rule: TrafficClassificationRule, utm_params: Dict, referrer: str) -> bool:
        conditions = rule.conditions
        
        if 'utm_source' in conditions:
            allowed_sources = conditions['utm_source']
            if utm_params.get('utm_source', '').lower() not in [s.lower() for s in allowed_sources]:
                return False
        
        if 'utm_medium' in conditions:
            allowed_mediums = conditions['utm_medium']
            if utm_params.get('utm_medium', '').lower() not in [m.lower() for m in allowed_mediums]:
                return False
        
        if conditions.get('has_campaign_id', False):
            if not utm_params.get('utm_campaign') and not utm_params.get('utm_id'):
                return False
        
        if 'referrer_domain' in conditions and referrer:
            domain = urlparse(referrer).netloc
            allowed_domains = conditions['referrer_domain']
            if not any(d in domain for d in allowed_domains):
                return False
        
        return True
    
    @staticmethod
    def is_paid_advertising(traffic_type: str) -> bool:
        return traffic_type == 'paid_ads'