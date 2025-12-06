from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from decimal import Decimal


class UTMParameterSchema(BaseModel):
    key: str = Field(..., min_length=1, max_length=50)
    value: str = Field(..., min_length=1, max_length=255)


class CreateCampaignRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    google_ads_campaign_id: Optional[str] = Field(None, max_length=100)
    google_ads_customer_id: Optional[str] = Field(None, max_length=50)
    utm_params: Optional[List[UTMParameterSchema]] = []

    @validator('utm_params')
    def validate_utm_params(cls, v):
        if v:
            keys = [param.key for param in v]
            if len(keys) != len(set(keys)):
                raise ValueError('Duplicate UTM parameter keys are not allowed')
        return v


class UpdateCampaignRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    google_ads_campaign_id: Optional[str] = Field(None, max_length=100)
    google_ads_customer_id: Optional[str] = Field(None, max_length=50)
    utm_params: Optional[List[UTMParameterSchema]] = None
    is_archived: Optional[bool] = None

    @validator('utm_params')
    def validate_utm_params(cls, v):
        if v:
            keys = [param.key for param in v]
            if len(keys) != len(set(keys)):
                raise ValueError('Duplicate UTM parameter keys are not allowed')
        return v


class CampaignResponse(BaseModel):
    id: str
    name: str
    google_ads_campaign_id: Optional[str] = None
    google_ads_customer_id: Optional[str] = None
    total_impressions: int
    total_clicks: int
    total_cost_micros: int
    total_emissions_kg: float
    last_synced_at: Optional[str] = None
    is_archived: bool
    created_at: str
    updated_at: str
    utm_params: List[Dict[str, str]] = []