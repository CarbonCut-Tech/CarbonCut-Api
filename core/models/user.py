import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal

@dataclass
class User:
    id: str
    email: str
    name: Optional[str] = None
    phone_number: Optional[str] = None
    company_name: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    otp_code: Optional[str] = None
    otp_expiry: Optional[datetime] = None
    otp_verified: bool = False
    is_active: bool = True
    onboarded: bool = False
    industry_id: Optional[str] = None
    extras: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OTPRequest:
    email: str
    otp_code: str
    expiry: datetime
    created_at: datetime = field(default_factory=datetime.now)
    
@dataclass
class AuthToken:
    user_id: str
    email: str
    token: str
    issued_at: datetime
    expires_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OAuthCredential:
    id: str
    user_id: str
    provider: str  
    provider_user_id: str
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    scopes: list = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    extras: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.now() >= self.expires_at
    
    def needs_refresh(self) -> bool:
        if not self.expires_at:
            return False
        from datetime import timedelta
        return datetime.now() >= (self.expires_at - timedelta(minutes=5))
@dataclass
class CloudProviderConfig:
    provider_name: str
    api_key: str
    secret_key: str
    region: str
    account_id: str
    extras: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CDNConfig:
    cdn_provider: str
    api_key: str
    domain: str
    ttl: int  # Time to live in seconds
    extras: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkforceConfig:
    enable_travel: bool
    travel_policy: str
    remote_work_enabled: bool
    office_location: Optional[str] = None
    extras: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OnPremConfig:
    server_id: str
    ip_address: str
    location: str
    capacity: Decimal
    current_usage: Decimal
    extras: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UserEmissionProfile:
    user_id: str
    cloud_providers: List[CloudProviderConfig]
    cdn_configs: List[CDNConfig]
    workforce_config: WorkforceConfig
    onprem_configs: List[OnPremConfig]
    reporting_period: str  
    emission_scope_enabled: Dict[str, bool]  
    created_at: datetime
    updated_at: datetime