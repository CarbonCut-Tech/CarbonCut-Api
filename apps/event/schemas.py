from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class UTMParams(BaseModel):
    utm_id: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None


class EventRequest(BaseModel):
    event_type: str = Field(..., alias='event')
    session_id: str
    event_time: datetime = Field(..., alias='timestamp')
    api_key: str = Field(..., alias='tracker_token')
    
    page_url: Optional[str] = None
    referrer: Optional[str] = None
    user_agent: Optional[str] = None
    event_id: Optional[str] = None
    user_id: Optional[str] = None
    
    utm_param: Optional[Dict[str, Any]] = Field(default_factory=dict, alias='utm_params')
    
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_accuracy: Optional[float] = None
    
    bytes_per_page_view: Optional[int] = None
    bytes_per_click: Optional[int] = None
    bytes_per_conversion: Optional[int] = None
    encoded_size: Optional[int] = None
    decoded_size: Optional[int] = None
    tracking_request_bytes: Optional[int] = None
    tracking_request_body: Optional[int] = None
    resource_count: Optional[int] = None
    resource_types: Optional[Dict[str, int]] = None
    screen_resolution: Optional[str] = None
    
    conversion_type: Optional[str] = None
    conversion_label: Optional[str] = None
    conversion_url: Optional[str] = None
    conversion_rule_id: Optional[str] = None
    conversion_value: Optional[float] = None
    currency: Optional[str] = None
    match_type: Optional[str] = None
    pattern: Optional[str] = None

    class Config:
        populate_by_name = True


class EventResponse(BaseModel):
    success: bool
    message: str
    task_id: Optional[str] = None
    location_captured: Optional[bool] = None
    location_source: Optional[str] = None
    session_id: Optional[str] = None
    external_id: Optional[str] = None