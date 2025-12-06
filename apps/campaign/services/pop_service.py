import logging
from typing import Optional, Dict, List
from django.core.cache import cache
from django.db.models import F
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from geopy.distance import geodesic

from ..models import PointOfPresence

logger = logging.getLogger(__name__)


class PopService:
    CACHE_TTL = 86400  
    CACHE_KEY_NEAREST = "pop_nearest_{lat}_{lon}"
    CACHE_KEY_ALL = "pop_all_active"
    
    @classmethod
    def find_nearest_pop(cls, latitude: float, longitude: float) -> Optional[Dict]:
        cache_key = cls.CACHE_KEY_NEAREST.format(
            lat=round(latitude, 4),
            lon=round(longitude, 4)
        )
        
        cached = cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for nearest PoP: {cached['name']}")
            return cached
        
        user_point = Point(longitude, latitude, srid=4326)
        
        try:
            nearest = PointOfPresence.objects.filter(
                is_active=True
            ).annotate(
                distance_m=Distance('coordinates', user_point)
            ).order_by('distance_m').values(
                'pop_id', 'name', 'location', 'latitude', 'longitude',
                'region', distance_m=F('distance_m')
            ).first()
            
            if not nearest:
                logger.warning("No active PoPs found")
                return None
            
            distance_km = geodesic(
                (latitude, longitude),
                (nearest['latitude'], nearest['longitude'])
            ).kilometers
            
            result = {
                'pop_id': nearest['pop_id'],
                'name': nearest['name'],
                'location': nearest['location'],
                'lat': nearest['latitude'],
                'lon': nearest['longitude'],
                'region': nearest['region'],
                'distance_km': round(distance_km, 2)
            }
            
            cache.set(cache_key, result, cls.CACHE_TTL)
            
            logger.debug(f"Nearest PoP: {result['name']} ({result['distance_km']}km)")
            return result
            
        except Exception as e:
            logger.error(f"Error finding nearest PoP: {e}", exc_info=True)
            return cls._get_fallback_pop(latitude, longitude)
    
    @classmethod
    def get_all_active_pops(cls) -> List[Dict]:
        cached = cache.get(cls.CACHE_KEY_ALL)
        if cached:
            return cached
        
        pops = list(PointOfPresence.objects.filter(
            is_active=True
        ).values(
            'pop_id', 'name', 'location', 'latitude', 'longitude', 'region'
        ))
        
        cache.set(cls.CACHE_KEY_ALL, pops, cls.CACHE_TTL)
        return pops
    
    @classmethod
    def _get_fallback_pop(cls, latitude: float, longitude: float) -> Dict:
        fallback_hubs = [
            {'pop_id': 'ashburn-va', 'lat': 39.0438, 'lon': -77.4874, 'name': 'Ashburn VA'},
            {'pop_id': 'frankfurt-de', 'lat': 50.1109, 'lon': 8.6821, 'name': 'Frankfurt DE'},
            {'pop_id': 'singapore', 'lat': 1.3521, 'lon': 103.8198, 'name': 'Singapore'},
            {'pop_id': 'sydney-au', 'lat': -33.8688, 'lon': 151.2093, 'name': 'Sydney AU'},
        ]
        
        nearest = min(
            fallback_hubs,
            key=lambda p: geodesic((latitude, longitude), (p['lat'], p['lon'])).kilometers
        )
        
        distance_km = geodesic(
            (latitude, longitude),
            (nearest['lat'], nearest['lon'])
        ).kilometers
        
        logger.warning(f"Using fallback PoP: {nearest['name']} ({distance_km:.1f}km)")
        
        return {
            **nearest,
            'location': nearest['name'],
            'region': 'unknown',
            'distance_km': round(distance_km, 2)
        }
    
    @classmethod
    def clear_cache(cls):
        cache.delete_pattern("pop_*")
        logger.info("PoP cache cleared")