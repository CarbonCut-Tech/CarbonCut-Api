from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID


class UTMParameter(BaseModel):
    key: str
    value: str


class Campaign(BaseModel):
    id: Optional[int] = None
    external_id: Optional[UUID] = None
    user_id: str
    name: str
    
    google_ads_campaign_id: Optional[str] = None
    google_ads_customer_id: Optional[str] = None
    
    total_impressions: int = 0
    total_clicks: int = 0
    total_cost_micros: int = 0
    total_emissions_kg: Decimal = Decimal('0.000000')
    
    utm_params: List[UTMParameter] = []

    last_synced_at: Optional[datetime] = None

    is_archived: bool = False

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            Decimal: str,
            UUID: str,
            datetime: lambda v: v.isoformat() if v else None,
        }


class CampaignEmission(BaseModel):
    id: Optional[int] = None
    external_id: Optional[UUID] = None
    campaign_id: int
    
    date: date
    hour: Optional[int] = None
    
    country: str = 'United States'
    region: str = ''
    city: str = ''
    device_type: str = 'desktop'
    
    page_views: int = 0
    clicks: int = 0
    conversions: int = 0
    sessions: int = 0
    
    impressions: int = 0
    ad_clicks: int = 0
    cost_micros: int = 0
    
    impression_emissions_g: Decimal = Decimal('0.000000')
    page_view_emissions_g: Decimal = Decimal('0.000000')
    click_emissions_g: Decimal = Decimal('0.000000')
    conversion_emissions_g: Decimal = Decimal('0.000000')
    total_emissions_g: Decimal = Decimal('0.000000')
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            Decimal: str,
            UUID: str,
            datetime: lambda v: v.isoformat() if v else None,
            date: lambda v: v.isoformat() if v else None,
        }


class CreateCampaignRequest(BaseModel):
    name: str
    google_ads_campaign_id: Optional[str] = None
    google_ads_customer_id: Optional[str] = None
    utm_params: List[UTMParameter] = []


class UpdateCampaignRequest(BaseModel):
    name: Optional[str] = None
    utm_params: Optional[List[UTMParameter]] = None


class GoogleAdsImpressionData(BaseModel):
    date: date
    country: str
    device_type: str
    impressions: int
    clicks: int
    cost_micros: int