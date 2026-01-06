from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal


@dataclass
class CloudProviderConfig:
    id: str
    user_id: str
    provider: str  # 'aws', 'gcp', 'azure'
    connection_type: str  # 'csv_upload', 'api', 'cost_estimate'
    regions: List[str] = field(default_factory=list)
    monthly_cost_usd: Optional[Decimal] = None
    has_csv_data: bool = False
    last_csv_upload_date: Optional[datetime] = None
    csv_file_path: Optional[str] = None
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class CDNConfig:
    id: str
    user_id: str
    provider: str  # 'cloudflare', 'aws_cloudfront', 'akamai', 'generic'
    connection_type: str  # 'manual', 'api'
    monthly_gb_transferred: Optional[Decimal] = None
    regions: List[str] = field(default_factory=list)
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class OfficeLocation:
    city: str
    country: str
    country_code: str  # For grid factor lookup
    square_meters: Optional[Decimal] = None
    employee_count: Optional[int] = None


@dataclass
class WorkforceConfig:
    id: str
    user_id: str
    total_employees: int
    remote_employee_percentage: Decimal  # 0.0 to 1.0
    office_locations: List[OfficeLocation] = field(default_factory=list)
    travel_tracking_enabled: bool = False
    last_travel_upload_date: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ServerSpec:
    name: str
    cpu_cores: int
    ram_gb: int
    storage_tb: Decimal
    avg_cpu_utilization: Decimal  # 0.0 to 1.0
    hours_per_day: Decimal = Decimal('24')
    days_per_month: int = 30


@dataclass
class OnPremConfig:
    id: str
    user_id: str
    server_specs: List[ServerSpec]
    location_city: str
    location_country_code: str  # For grid factor
    power_usage_effectiveness: Decimal = Decimal('1.6')  # PUE
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class UserEmissionProfile:
    user_id: str
    cloud_providers: List[CloudProviderConfig] = field(default_factory=list)
    cdn_configs: List[CDNConfig] = field(default_factory=list)
    workforce_config: Optional[WorkforceConfig] = None
    onprem_configs: List[OnPremConfig] = field(default_factory=list)
    reporting_period: str = 'monthly'  # 'monthly', 'quarterly', 'annual'
    emission_scope_enabled: Dict[str, bool] = field(default_factory=lambda: {
        'scope_1': True,
        'scope_2': True,
        'scope_3': True
    })
    onboarding_completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class SubscriptionTier:
    tier_name: str  # 'starter', 'pro'
    max_cloud_providers: int
    cdn_tracking_enabled: bool
    onprem_tracking_enabled: bool
    travel_csv_uploads: bool
    multi_cloud_enabled: bool
    api_access_enabled: bool
    export_formats: List[str] = field(default_factory=list)
    csrd_compliance_enabled: bool = False