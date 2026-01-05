from apps.apikey.models import IndustryCategory, Product
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class CreateAPIKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(default='*', max_length=255)
    industry_category: Optional[IndustryCategory] = None
    product: Optional[Product] = None

class APIKeyResponse(BaseModel):
    id: str
    name: str
    prefix: str
    domain: str
    is_active: bool
    industry_category: Optional[str] = None
    product: Optional[str] = None
    last_used_at: Optional[str] = None
    created_at: str
    conversion_rules_count: int


class APIKeyDetailResponse(BaseModel):
    id: str
    name: str
    domain: str
    is_active: bool
    created_at: str
    prefix: str
    full_key: Optional[str] = None


class CreateConversionRuleRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    rule_type: str = Field(..., pattern='^(url|click|form_submit|custom_event)$')
    url_pattern: Optional[str] = None
    match_type: Optional[str] = Field(default='contains', pattern='^(exact|contains|starts_with|ends_with|regex|query_param)$')
    css_selector: Optional[str] = None
    element_text: Optional[str] = None
    form_id: Optional[str] = None
    custom_event_name: Optional[str] = None
    track_value: bool = False
    value_selector: Optional[str] = None
    default_value: Optional[Decimal] = None
    priority: int = Field(default=0, ge=0)

    @validator('url_pattern')
    def validate_url_pattern(cls, v, values):
        if values.get('rule_type') == 'url' and not v:
            raise ValueError('URL pattern is required for URL rules')
        return v

    @validator('css_selector')
    def validate_css_selector(cls, v, values):
        if values.get('rule_type') == 'click' and not v:
            raise ValueError('CSS selector is required for click rules')
        return v

    @validator('form_id')
    def validate_form_id(cls, v, values):
        if values.get('rule_type') == 'form_submit' and not v:
            raise ValueError('Form ID is required for form submit rules')
        return v

    @validator('custom_event_name')
    def validate_custom_event_name(cls, v, values):
        if values.get('rule_type') == 'custom_event' and not v:
            raise ValueError('Event name is required for custom event rules')
        return v


class UpdateConversionRuleRequest(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(default=None, ge=0)
    url_pattern: Optional[str] = None
    match_type: Optional[str] = None
    css_selector: Optional[str] = None
    element_text: Optional[str] = None


class ConversionRuleResponse(BaseModel):
    id: str
    name: str
    rule_type: str
    priority: int
    is_active: bool
    conversion_count: int
    last_triggered_at: Optional[str] = None
    created_at: str
    url_pattern: Optional[str] = None
    match_type: Optional[str] = None
    css_selector: Optional[str] = None
    element_text: Optional[str] = None
    form_id: Optional[str] = None
    custom_event_name: Optional[str] = None
    track_value: Optional[bool] = None
    value_selector: Optional[str] = None
    default_value: Optional[float] = None


class VerifyInstallationRequest(BaseModel):
    url: str = Field(..., min_length=1)


class InstallationInstructions(BaseModel):
    script_tag: str
    npm_command: str
    installation_steps: List[str]
    verification_url: str


class VerificationResponse(BaseModel):
    installed: bool
    script_found: bool
    api_key_valid: bool
    errors: Optional[List[str]] = None
    installation_guide: Optional[InstallationInstructions] = None