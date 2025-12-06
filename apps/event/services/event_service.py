import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from django.db import transaction
from django.utils import timezone
from dateutil import parser

from ..models import Session
from apps.apikey.models import APIKey
from .event_validation_service import EventValidationService, EventValidationError

logger = logging.getLogger(__name__)


class EventService:
    @staticmethod
    def get_or_create_session(
        session_id: str,
        api_key: APIKey,
        event_time: datetime,
        event_dict: Dict[str, Any],
        utm_param: Dict[str, Any],
        location_data: Dict[str, str],
        device_type: str,
        user_agent: str,
        ip_address: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        location_accuracy: Optional[float] = None,
        location_source: str = 'ip_geolocation'
    ) -> tuple[Session, bool]:
        country = location_data.get('country', 'United States')
        city = location_data.get('city', '')
        state = location_data.get('state', '')
        utm_id = utm_param.get('utm_id')
        
        session, created = Session.objects.get_or_create(
            session_id=session_id,
            api_key=api_key,
            defaults={
                'external_id': uuid.uuid4(),
                'campaign_id': None,
                'utm_id': utm_id,
                'first_event': event_time,
                'last_event': event_time,
                'user_agent': user_agent,
                'ip_address': ip_address,
                'country': country,
                'city': city,
                'state': state,
                'device_type': device_type,
                'latitude': latitude,
                'longitude': longitude,
                'location_accuracy': location_accuracy,
                'location_source': location_source,
                'events': [event_dict],
                'status': Session.SessionStatus.ACTIVE,
            }
        )
        
        return session, created
    
    @staticmethod
    def update_session(
        session: Session,
        event_time: datetime,
        event_dict: Dict[str, Any],
        event_type: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        location_accuracy: Optional[float] = None,
        location_source: str = None,
        city: str = '',
        state: str = ''
    ) -> bool:
        should_schedule_task = False
        
        with transaction.atomic():
            locked_session = Session.objects.select_for_update().get(pk=session.pk)
            
            was_closed = locked_session.status == Session.SessionStatus.CLOSED
            if was_closed:
                locked_session.status = Session.SessionStatus.ACTIVE
                should_schedule_task = True
                logger.info(f"Reopening closed session {session.session_id}")
            
            locked_session.last_event = max(locked_session.last_event, event_time)
            
            if latitude and longitude and location_source == 'browser_geolocation':
                if locked_session.location_source != 'browser_geolocation':
                    locked_session.latitude = latitude
                    locked_session.longitude = longitude
                    locked_session.city = city
                    locked_session.state = state
                    locked_session.location_accuracy = location_accuracy
                    locked_session.location_source = location_source
                    logger.info(f"Upgraded session {session.session_id} to browser geolocation")
            
            if event_type == "conversion" and locked_session.conversion_event is None:
                locked_session.conversion_event = event_time
            
            if locked_session.events is None:
                locked_session.events = []
            locked_session.events.append(event_dict)
            
            locked_session.save()
        
        return should_schedule_task
    
    @staticmethod
    def build_event_dict(
        event_type: str,
        event_time: datetime,
        event_data: dict,
        user_agent: str,
        ip_address: str,
        utm_param: dict,
        location_data: dict,
        device_type: str,
        bytes_data: dict,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        screen_resolution: str = ''
    ) -> Dict[str, Any]:
        event_dict = {
            'event_type': event_type,
            'event_time': event_time.isoformat(),
            'page_url': event_data.get('page_url', ''),
            'referrer': event_data.get('referrer', ''),
            'user_agent': user_agent,
            'utm_param': utm_param,
            'ip_address': ip_address,
            'country': location_data.get('country', 'United States'),
            'city': location_data.get('city', ''),
            'state': location_data.get('state', ''),
            'latitude': latitude,
            'longitude': longitude,
            'device_type': device_type,
            'bytes_data': bytes_data,
            'screen_resolution': screen_resolution,
        }
        
        if event_type == 'conversion':
            event_dict.update({
                'conversion_type': event_data.get('conversion_type'),
                'conversion_label': event_data.get('conversion_label'),
                'conversion_url': event_data.get('conversion_url'),
                'conversion_rule_id': event_data.get('conversion_rule_id'),
                'match_type': event_data.get('match_type'),
                'pattern': event_data.get('pattern'),
            })
        
        return event_dict
    
    @staticmethod
    def parse_event_time(event_time) -> datetime:
        if isinstance(event_time, str):
            return parser.parse(event_time)
        return event_time