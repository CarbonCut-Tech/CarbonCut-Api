from decimal import Decimal
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
from domain.base import BaseEventProcessor, EventProcessingResult
from domain.registry import EventProcessorRegistry
from calculators import InternetAdsCalculator, Platform, AdFormat


class AdsEventPayload(BaseModel):
    event: str
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
    
    platform: Optional[str] = None
    campaign_id: Optional[str] = None
    ad_id: Optional[str] = None
    ad_format: Optional[str] = None
    
    class Config:
        populate_by_name = True
        extra = 'allow'


class InternetAdsProcessor(BaseEventProcessor):
    @property
    def event_type(self) -> str:
        return "internet_ads"
    
    def validate_payload(self, payload: dict) -> dict:
        validated = AdsEventPayload(**payload)
        return validated.dict()
    
    def process(self, payload: dict) -> EventProcessingResult:
        calculator = InternetAdsCalculator()

        # parse payload with pydantic
        utm_params = payload.get('utm_params', {})

        platform = self._extract_platform(utm_params)

        campaign_id = (
            utm_params.get('utm_campaign') or 
            payload.get('campaign_id') or 
            payload.get('session_id')
        )
        
        ad_id = (
            utm_params.get('utm_content') or 
            utm_params.get('utm_term') or
            payload.get('event_id')
        )
        
        ad_format = self._determine_ad_format(payload.get('event', 'page_view'))
        
        device_type = self._detect_device_type(
            payload.get('user_agent', ''),
            payload.get('screen_resolution', '')
        )
        
        country_code = 'US'
        if payload.get('geolocation'):
            country_code = 'US'
        
        calc_input = {
            'platform': platform,
            'ad_format': ad_format,
            'impressions': 1,  # Each event is one impression
            'device_type': device_type,
            'country_code': country_code
        }
        
        result = calculator.calculate(calc_input)
        
        return EventProcessingResult(
            kg_co2_emitted=Decimal(str(result['total_emissions_kg'])),
            reference_id=payload['event_id'],
            reference_type=f'internet_ads_{platform}',
            metadata={
                'event_type': payload.get('event'),
                'campaign_id': campaign_id,
                'ad_id': ad_id,
                'platform': platform,
                'ad_format': ad_format,
                'device_type': device_type,
                'utm_params': utm_params,
                'page_url': payload.get('page_url'),
                'breakdown': result['breakdown']
            }
        )
    
    def _extract_platform(self, utm_params: dict) -> str:
        """Extract ad platform from UTM params"""
        utm_source = utm_params.get('utm_source', '').lower()
        
        if 'google' in utm_source or 'adwords' in utm_source:
            return 'google_ads'
        elif 'facebook' in utm_source or 'meta' in utm_source or 'fb' in utm_source:
            return 'meta'
        elif 'linkedin' in utm_source:
            return 'linkedin'
        elif 'twitter' in utm_source or 'x.com' in utm_source:
            return 'twitter'
        elif 'tiktok' in utm_source:
            return 'tiktok'
        else:
            return 'google_ads'  
    
    def _determine_ad_format(self, event_type: str) -> str:
        """Determine ad format from event type"""
        if event_type == 'page_view':
            return 'display'
        elif event_type == 'click':
            return 'search'
        elif event_type == 'conversion':
            return 'shopping'
        elif event_type == 'ping':
            return 'video'
        else:
            return 'display'  # Default
    
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


# Register the unified processor
EventProcessorRegistry.register(InternetAdsProcessor)