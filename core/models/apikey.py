from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

@dataclass
class APIKey:
    id: str
    key: str
    name: str
    user_id: str
    is_active: bool = True
    usage_count: int = 0
    last_used_at: Optional[datetime] = None
    domain: str = '*'
    industry_category: Optional[str] = None
    product: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class ConversionRule:
    id: str
    api_key_id: str
    rule_type: str  # 'url', 'click', 'form_submit', 'custom_event'
    name: str
    match_type: str = 'contains'
    url_pattern: Optional[str] = None
    css_selector: Optional[str] = None
    element_text: Optional[str] = None
    form_id: Optional[str] = None
    custom_event_name: Optional[str] = None
    track_value: bool = False
    value_selector: Optional[str] = None
    default_value: Optional[Decimal] = None
    priority: int = 0
    is_active: bool = True
    conversion_count: int = 0
    last_triggered_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)