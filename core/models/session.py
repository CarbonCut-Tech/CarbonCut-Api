from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from decimal import Decimal

@dataclass
class SessionEvent:
    event_type: str
    timestamp: datetime
    page_url: str = ''
    referrer: str = ''
    metadata: dict = field(default_factory=dict)

@dataclass
class Session:
    session_id: str
    user_id: str
    started_at: datetime
    last_activity: datetime
    events: List[SessionEvent] = field(default_factory=list)
    status: str = 'active'
    device_type: str = 'desktop'
    country: str = ''
    campaign_id: Optional[str] = None
    user_agent: str = ''
    ip_address: str = ''
    
    def is_active(self) -> bool:
        return self.status == 'active'
    
    def add_event(self, event: SessionEvent):
        self.events.append(event)
        self.last_activity = event.timestamp
    
    def close(self):
        self.status = 'closed'
    
    def duration_seconds(self) -> float:
        return (self.last_activity - self.started_at).total_seconds()
    
    def event_count(self) -> int:
        return len(self.events)