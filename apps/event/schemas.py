from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

class CloudProviderInput(BaseModel):
    provider: str = Field(..., description="Cloud provider: aws, gcp, azure")
    connection_method: str = Field(..., description="csv_upload, api, cost_estimate")
    regions: List[str] = Field(default_factory=list)
    monthly_cost_usd: Optional[Decimal] = Field(None, ge=0, description="Estimated monthly cost")
    
    @validator('provider')
    def validate_provider(cls, v):
        allowed = ['aws', 'gcp', 'azure']
        if v.lower() not in allowed:
            raise ValueError(f"Provider must be one of {allowed}")
        return v.lower()
    
    @validator('connection_method')
    def validate_connection_method(cls, v):
        allowed = ['csv_upload', 'api', 'cost_estimate']
        if v.lower() not in allowed:
            raise ValueError(f"Connection method must be one of {allowed}")
        return v.lower()


class CloudProviderResponse(BaseModel):
    id: str
    provider: str
    connection_type: str
    regions: List[str]
    monthly_cost_usd: Optional[float]
    has_csv_data: bool
    last_csv_upload_date: Optional[str]
    is_active: bool
    created_at: str
class CDNProviderInput(BaseModel):
    provider: str = Field(..., description="CDN provider: cloudflare, aws_cloudfront, akamai, fastly, generic")
    monthly_gb_transferred: Optional[Decimal] = Field(None, ge=0, description="Monthly GB transferred")
    regions: List[str] = Field(default_factory=list, description="Regions served")
    
    @validator('provider')
    def validate_provider(cls, v):
        allowed = ['cloudflare', 'aws_cloudfront', 'akamai', 'fastly', 'generic']
        if v.lower() not in allowed:
            raise ValueError(f"CDN provider must be one of {allowed}")
        return v.lower()
class CDNProviderResponse(BaseModel):
    id: str
    provider: str
    monthly_gb_transferred: Optional[float]
    regions: List[str]
    is_active: bool
    created_at: str
class OfficeLocationInput(BaseModel):
    city: str = Field(..., min_length=1)
    country: str = Field(..., min_length=1)
    country_code: str = Field(..., min_length=2, max_length=2, description="ISO 2-letter country code")
    square_meters: Optional[Decimal] = Field(None, ge=0)
    employee_count: Optional[int] = Field(None, ge=0)
    
    @validator('country_code')
    def validate_country_code(cls, v):
        return v.upper()
class WorkforceInput(BaseModel):
    total_employees: int = Field(..., ge=1, description="Total number of employees")
    remote_percentage: Decimal = Field(..., ge=0, le=100, description="Percentage of remote employees (0-100)")
    office_locations: List[OfficeLocationInput] = Field(default_factory=list)
    track_travel: bool = Field(default=False)
    
    @validator('remote_percentage')
    def validate_remote_percentage(cls, v):
        if v < 0 or v > 100:
            raise ValueError("Remote percentage must be between 0 and 100")
        return v
class WorkforceResponse(BaseModel):
    id: str
    total_employees: int
    remote_percentage: float
    office_locations: List[Dict[str, Any]]
    travel_tracking_enabled: bool
    last_travel_upload_date: Optional[str]
    created_at: str
class OnPremServerInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    cpu_cores: int = Field(..., ge=1, le=256)
    ram_gb: int = Field(..., ge=1, le=2048)
    storage_tb: Decimal = Field(..., ge=0, le=1000)
    avg_cpu_utilization: Decimal = Field(default=Decimal('50'), ge=0, le=100, description="Average CPU utilization %")
    hours_per_day: Decimal = Field(default=Decimal('24'), ge=0, le=24)
    days_per_month: int = Field(default=30, ge=1, le=31)
    location_city: str = Field(...)
    location_country_code: str = Field(..., min_length=2, max_length=2)
    power_usage_effectiveness: Decimal = Field(default=Decimal('1.6'), ge=1.0, le=3.0, description="PUE factor")
    
    @validator('location_country_code')
    def validate_country_code(cls, v):
        return v.upper()


class OnPremServerResponse(BaseModel):
    id: str
    server_name: str
    cpu_cores: int
    ram_gb: int
    storage_tb: float
    avg_cpu_utilization: float
    location_city: str
    location_country_code: str
    is_active: bool
    created_at: str
class EmissionSourcesOnboardingRequest(BaseModel):
    cloud_providers: List[CloudProviderInput] = Field(default_factory=list)
    
    cdn_providers: List[CDNProviderInput] = Field(default_factory=list)
    workforce: Optional[WorkforceInput] = None
    
    onprem_servers: List[OnPremServerInput] = Field(default_factory=list)
    website_tracking_enabled: bool = Field(default=True)
    
    @validator('cloud_providers')
    def validate_cloud_providers(cls, v):
        # Check for duplicate providers
        providers = [cp.provider for cp in v]
        if len(providers) != len(set(providers)):
            raise ValueError("Duplicate cloud providers not allowed")
        return v
class EmissionSourcesUpdateRequest(BaseModel):
    cloud_providers: Optional[List[CloudProviderInput]] = None
    cdn_providers: Optional[List[CDNProviderInput]] = None
    workforce: Optional[WorkforceInput] = None
    onprem_servers: Optional[List[OnPremServerInput]] = None

class EmissionSourcesResponse(BaseModel):
    user_id: str
    cloud_providers: List[CloudProviderResponse]
    cdn_providers: List[CDNProviderResponse]
    workforce: Optional[WorkforceResponse]
    onprem_servers: List[OnPremServerResponse]
    onboarding_completed: bool
    created_at: Optional[str]
    updated_at: Optional[str]
class CloudCSVUploadRequest(BaseModel):
    provider: str = Field(..., description="aws, gcp, or azure")
    file_name: str
    @validator('provider')
    def validate_provider(cls, v):
        allowed = ['aws', 'gcp', 'azure']
        if v.lower() not in allowed:
            raise ValueError(f"Provider must be one of {allowed}")
        return v.lower()
class TravelCSVUploadRequest(BaseModel):
    file_name: str
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2020, le=2030)
class CSVUploadResponse(BaseModel):
    success: bool
    message: str
    records_processed: int = 0
    total_emissions_kg: float = 0
    errors: List[str] = Field(default_factory=list)
class ScopeBreakdown(BaseModel):
    kg_co2: float
    percentage: float
class SourceBreakdown(BaseModel):
    kg_co2: float
    scope: str
    accuracy: str
class EmissionSummaryResponse(BaseModel):
    user_id: str
    month: int
    year: int
    total_emissions_kg: float
    scope_breakdown: Dict[str, ScopeBreakdown]
    source_breakdown: Dict[str, SourceBreakdown]
    trends: Optional[Dict[str, Any]] = None
    recommendations: List[str] = Field(default_factory=list)


class EmissionsBySourceResponse(BaseModel):
    user_id: str
    period: str
    sources: Dict[str, float]
    total_kg: float


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