import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.dateparse import parse_datetime

from .schemas import EventRequest, EventResponse
from .services.location_service import LocationService
from .services.device_service import DeviceService
from .services.event_validation_service import EventValidationError
from .tasks import handle_event

logger = logging.getLogger(__name__)


class EventTrackingView(APIView):
    permission_classes = []  
    
    def post(self, request):
        try:
            event_data = request.data.copy()
            field_mappings = {
                'event': 'event_type',
                'timestamp': 'event_time',
                'tracker_token': 'api_key',
                'utm_params': 'utm_param'
            }
            
            for old_key, new_key in field_mappings.items():
                if old_key in event_data and new_key not in event_data:
                    event_data[new_key] = event_data.pop(old_key)

            if 'api_key' not in event_data:
                api_key_header = request.headers.get('X-Tracker-Token') or request.headers.get('X-API-Key')
                if api_key_header:
                    event_data['api_key'] = api_key_header
            
            if isinstance(event_data.get('event_time'), str):
                event_data['event_time'] = parse_datetime(event_data['event_time'])
            
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            latitude, longitude, location_accuracy = LocationService.extract_browser_location(event_data)
            
            if latitude and longitude:
                location_data = LocationService.reverse_geocode_sync(latitude, longitude)
                location_source = 'browser_geolocation'
                logger.info(
                    f"Browser location captured: {latitude:.4f}, {longitude:.4f} → "
                    f"{location_data.get('city', 'Unknown')}, {location_data.get('country', 'Unknown')}"
                )
            else:
                location_data = LocationService.get_location_from_ip(ip_address)
                location_source = 'ip_geolocation'
            
            device_type = DeviceService.detect_device_type(
                user_agent,
                event_data.get('screen_resolution')
            )
            
            logger.info(
                f"Event received | Type: {event_data.get('event_type')} | "
                f"IP: {ip_address} | "
                f"Location: {location_data.get('city', '')}, {location_data.get('country', 'Unknown')} | "
                f"Source: {location_source} | "
                f"Device: {device_type} | "
                f"Session: {event_data.get('session_id')}"
            )
            
            request_data = {
                'ip_address': ip_address,
                'location_data': location_data,
                'latitude': latitude,
                'longitude': longitude,
                'location_accuracy': location_accuracy,
                'location_source': location_source,
                'user_agent': user_agent,
                'device_type': device_type,
                'extra_data': {k: v for k, v in event_data.items() if k not in ['event_type', 'session_id', 'event_time', 'api_key', 'utm_param']}
            }
            
            result = handle_event.delay(event_data, request_data)
            
            response = EventResponse(
                success=True,
                message='Event received and queued for processing',
                task_id=str(result.id),
                location_captured=latitude is not None,
                location_source=location_source
            )
            
            return Response(response.dict(), status=status.HTTP_200_OK)
            
        except EventValidationError as e:
            logger.error(f"Event validation error: {e}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error processing event: {e}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_client_ip(self, request) -> str:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip