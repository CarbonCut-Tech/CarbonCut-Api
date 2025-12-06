import logging
import asyncio
from typing import Tuple, Optional, Dict

logger = logging.getLogger(__name__)


class LocationService:
    @staticmethod
    def extract_browser_location(event_data: dict) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        try:
            latitude = event_data.get('latitude')
            longitude = event_data.get('longitude')
            accuracy = event_data.get('location_accuracy')
            
            if latitude and longitude:
                lat = float(latitude)
                lon = float(longitude)
                
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    logger.warning(f"Invalid coordinates range: {lat}, {lon}")
                    return None, None, None
                
                return lat, lon, float(accuracy) if accuracy else None
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing browser location: {e}")
        
        return None, None, None
    
    @staticmethod
    async def reverse_geocode_async(latitude: float, longitude: float) -> Dict[str, str]:
        """Async reverse geocoding (implement with your geolocation service)"""
        # from apps.common.services.geolocation_service import GeolocationService
        # return await GeolocationService.reverse_geocode(latitude, longitude)
    
    @staticmethod
    def reverse_geocode_sync(latitude: float, longitude: float) -> Dict[str, str]:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # try:
            # from apps.common.services.geolocation_service import GeolocationService
            # return loop.run_until_complete(
                # GeolocationService.reverse_geocode(latitude, longitude)
            # )
        # finally:
            # loop.close()
    
    @staticmethod
    def get_location_from_ip(ip_address: str) -> Dict[str, str]:
        """Get location data from IP address"""
        # from apps.common.services.geolocation_service import GeolocationService
        # return GeolocationService.get_location(ip_address)