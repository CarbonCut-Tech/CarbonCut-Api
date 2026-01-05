from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

@dataclass
class ProcessedEvent:
    reference_id: str
    reference_type: str
    user_id: str
    event_type: str
    kg_co2_emitted: Decimal
    processed_at: datetime
    metadata: dict = field(default_factory=dict)

@dataclass
class ActiveSession:
    session_id: str
    user_id: str
    api_key: str
    last_event_at: datetime
    event_count: int = 0
    status: str = 'active'  
    created_at: datetime = field(default_factory=datetime.now)
    last_processed_at: Optional[datetime] = None