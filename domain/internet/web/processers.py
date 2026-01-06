from decimal import Decimal
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from domain.base import BaseEventProcessor, EventProcessingResult
from domain.registry import EventProcessorRegistry
from calculators.internet_website import InternetWebsiteCalculator
from apps.common.event_types import EventTypes
from domain.registry import event_processor
class SDKEventPayload(BaseModel):
    event: str = Field()
    session_id: str
    tracker_token: str
    event_id: str
    user_id: str
    page_url: str
    referrer: str = ""
    timestamp: datetime
    utm_params: dict = Field(default_factory=dict)
    
    user_agent: Optional[str] = None
    screen_resolution: Optional[str] = None
    viewport_size: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    page_title: Optional[str] = None
    
    bytesPerPageView: Optional[int] = None
    bytesPerClick: Optional[int] = None
    bytesPerConversion: Optional[int] = None
    encodedSize: Optional[int] = None
    decodedSize: Optional[int] = None
    resourceType: Optional[str] = None
    trackingRequestBytes: Optional[int] = None
    trackingRequestBody: Optional[int] = None
    resourceCount: Optional[int] = None
    resource_types: Optional[dict] = None
    
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_accuracy: Optional[float] = None
    geolocation: Optional[dict] = None
    
    conversion_type: Optional[str] = None
    conversion_label: Optional[str] = None
    conversion_url: Optional[str] = None
    conversion_rule_id: Optional[str] = None
    conversion_value: Optional[float] = None
    match_type: Optional[str] = None
    pattern: Optional[str] = None
    conversion_element: Optional[str] = None
    conversion_selector: Optional[str] = None
    element_text: Optional[str] = None
    
    time_spent_seconds: Optional[int] = None
    is_visible: Optional[bool] = None
    
    event_name: Optional[str] = None
    event_data: Optional[dict] = None
    custom_event_type: Optional[str] = None
    
    queuedAt: Optional[int] = None
    
    class Config:
        populate_by_name = True
        extra = 'allow'

@event_processor(EventTypes.INTERNET_WEB)
class InternetWebProcessor(BaseEventProcessor):
    @property
    def event_type(self) -> str:
        return EventTypes.INTERNET_WEB
    
    def validate_payload(self, payload: dict) -> dict:
        validated = SDKEventPayload(**payload)
        return validated.dict()
    
    def process(self, payload: dict) -> EventProcessingResult:
        calculator = InternetWebsiteCalculator()
        
        event_subtype = payload.get('event', 'page_view')
        
        bytes_transferred = self._get_bytes_transferred(payload, event_subtype)

        if bytes_transferred == 0:
            bytes_transferred = self._get_default_bytes(event_subtype)
        
        avg_page_size_mb = bytes_transferred / (1024 * 1024)
        
        device_type = self._detect_device_type(
            payload.get('user_agent', ''),
            payload.get('screen_resolution', '')
        )
        
        calc_input = {
            'bytes_transferred': bytes_transferred,
            'device_type': device_type,
            'country_code': 'US',  
            'session_duration_minutes': self._get_session_duration(payload, event_subtype)
        }
        
        result = calculator.calculate(calc_input)
        
        metadata = self._build_metadata(payload, event_subtype, device_type, bytes_transferred, avg_page_size_mb, result)
        
        return EventProcessingResult(
            kg_co2_emitted=Decimal(str(result['total_emissions_kg'])),
            reference_id=payload['event_id'],
            reference_type=f'internet_web_{event_subtype}',
            metadata=metadata
        )
    
    def _get_bytes_transferred(self, payload: dict, event_subtype: str) -> int:
        """Extract bytes transferred based on event type"""
        if event_subtype == 'page_view':
            return (
                payload.get('bytesPerPageView') or
                payload.get('decodedSize') or
                payload.get('encodedSize') or
                0
            )
        elif event_subtype == 'conversion':
            return payload.get('bytesPerConversion', 0)
        elif event_subtype == 'click':
            return payload.get('bytesPerClick', 0)
        else:
            return 0
    
    def _get_default_bytes(self, event_subtype: str) -> int:
        """Get realistic default bytes based on event type"""
        defaults = {
            'page_view': int(0.5 * 1024 * 1024),    # 500KB (realistic average)
            'click': int(5 * 1024),                  # 5KB (minimal AJAX request)
            'conversion': int(20 * 1024),            # 20KB (form submission)
            'ping': int(1 * 1024),                   # 1KB (heartbeat)
        }
        return defaults.get(event_subtype, int(0.5 * 1024 * 1024))
    
    def _get_session_duration(self, payload: dict, event_subtype: str) -> float:
        """Calculate session duration in minutes"""
        if event_subtype == 'ping':
            return (payload.get('time_spent_seconds', 0) / 60.0)
        elif event_subtype == 'conversion':
            return 0.1  # Minimal duration for conversion
        else:
            return 1.0  # Default 1 minute
    
    def _detect_device_type(self, user_agent: str, screen_resolution: str) -> str:
        """Detect device type from user agent and screen resolution"""
        if not user_agent:
            return 'desktop'
            
        user_agent_lower = user_agent.lower()
        
        if 'mobile' in user_agent_lower or 'android' in user_agent_lower:
            return 'mobile'
        elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
            return 'tablet'
        
        if screen_resolution:
            try:
                width = int(screen_resolution.split('x')[0])
                if width < 768:
                    return 'mobile'
                elif width < 1024:
                    return 'tablet'
            except:
                pass
        
        return 'desktop'
    
    def _build_metadata(self, payload: dict, event_subtype: str, device_type: str, 
                       bytes_transferred: int, avg_page_size_mb: float, calc_result: dict) -> dict:
        """Build metadata object based on event type"""
        
        # Common metadata for all events
        metadata = {
            'event_type': event_subtype,
            'session_id': payload['session_id'],
            'page_url': payload['page_url'],
            'referrer': payload.get('referrer'),
            'device_type': device_type,
            'utm_params': payload.get('utm_params', {}),
            'timestamp': payload['timestamp'].isoformat(),
            'breakdown': calc_result['breakdown'],
            'bytes_transferred': bytes_transferred,
            'page_size_mb': avg_page_size_mb,
        }
        
        # Add optional common fields
        if payload.get('page_title'):
            metadata['page_title'] = payload['page_title']
        if payload.get('user_agent'):
            metadata['user_agent'] = payload['user_agent']
        if payload.get('language'):
            metadata['language'] = payload['language']
        if payload.get('timezone'):
            metadata['timezone'] = payload['timezone']
        if payload.get('geolocation'):
            metadata['geolocation'] = payload['geolocation']
        
        # Add event-specific metadata
        if event_subtype == 'conversion':
            metadata.update({
                'conversion_type': payload.get('conversion_type'),
                'conversion_label': payload.get('conversion_label'),
                'conversion_value': payload.get('conversion_value'),
                'conversion_url': payload.get('conversion_url'),
                'conversion_rule_id': payload.get('conversion_rule_id'),
                'match_type': payload.get('match_type'),
                'pattern': payload.get('pattern'),
            })
        elif event_subtype == 'ping':
            metadata.update({
                'time_spent_seconds': payload.get('time_spent_seconds'),
                'is_visible': payload.get('is_visible'),
            })
        elif event_subtype == 'custom_event':
            metadata.update({
                'event_name': payload.get('event_name'),
                'event_data': payload.get('event_data'),
                'custom_event_type': payload.get('custom_event_type'),
            })
        
        return metadata

EventProcessorRegistry.register(InternetWebProcessor)