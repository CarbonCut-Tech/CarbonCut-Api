import logging
from typing import Dict, Optional
from django.core.cache import cache
from ..models import EmissionCoefficient

logger = logging.getLogger(__name__)


class CoefficientService:
    CACHE_TTL = 3600  
    
    @classmethod
    def get_coefficient(
        cls,
        name: str,
        component: str = None,
        traffic_type: str = 'both',
        device_type: str = None,
        network_type: str = None,
        platform: str = None
    ) -> Optional[float]:
        cache_key = f"coef_{name}_{component}_{traffic_type}_{device_type}_{network_type}_{platform}"
        cached_value = cache.get(cache_key)
        
        if cached_value is not None:
            return cached_value
        
        filters = {'name': name, 'is_active': True}
        
        if component:
            filters['component'] = component
        
        if traffic_type:
            filters['traffic_type__in'] = [traffic_type, 'both']
        
        if device_type:
            filters['device_type__in'] = [device_type, None]
        
        if network_type:
            filters['network_type__in'] = [network_type, None]
        
        if platform:
            filters['platform__in'] = [platform, None]
        
        coefficient = EmissionCoefficient.objects.filter(**filters).order_by(
            '-version',
            'device_type', 
            'network_type',
            'platform'
        ).first()
        
        if coefficient:
            value = coefficient.value
            cache.set(cache_key, value, cls.CACHE_TTL)
            return value
        
        logger.warning(f"Coefficient not found: {name} (filters: {filters})")
        return None
    
    @classmethod
    def get_device_power(cls, device_type: str, traffic_type: str = 'both') -> float:
        return cls.get_coefficient(
            name='device_power',
            component='device',
            traffic_type=traffic_type,
            device_type=device_type.lower()
        ) or 65.0  
    
    @classmethod
    def get_network_energy(cls, network_type: str = None, traffic_type: str = 'both') -> float:
        return cls.get_coefficient(
            name='network_energy_per_mb',
            component='network',
            traffic_type=traffic_type,
            network_type=network_type
        ) or 0.00015  
    
    @classmethod
    def get_adtech_energy(cls, platform: str = None) -> float:
        return cls.get_coefficient(
            name='adtech_energy_per_event',
            component='adtech',
            traffic_type='paid_ads',
            platform=platform
        ) or 1.5  
    
    @classmethod
    def invalidate_cache(cls):
        """Clear all coefficient caches"""
        cache.delete_pattern("coef_*")