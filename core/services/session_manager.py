from decimal import Decimal
from datetime import datetime
from typing import Optional
from ..models.session import Session, SessionEvent
from ..rules.session_rules import SessionRules

class SessionManager:
    def __init__(self):
        self.rules = SessionRules()
    
    def start_session(
        self, 
        session_id: str, 
        user_id: str,
        device_type: str = 'desktop',
        country: str = '',
        campaign_id: Optional[str] = None,
        user_agent: str = '',
        ip_address: str = ''
    ) -> Session:
        
        session = Session(
            session_id=session_id,
            user_id=user_id,
            started_at=datetime.now(),
            last_activity=datetime.now(),
            events=[],
            status='active',
            device_type=device_type,
            country=country,
            campaign_id=campaign_id,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        return session
    
    def track_activity(
        self, 
        session: Session, 
        event_type: str,
        page_url: str = '',
        referrer: str = '',
        metadata: dict = None
    ) -> Session:
        
        if not session.is_active():
            raise ValueError("Cannot track activity on closed session")
        
        event = SessionEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            page_url=page_url,
            referrer=referrer,
            metadata=metadata or {}
        )
        
        session.add_event(event)
        return session
    
    def should_close_session(self, session: Session) -> bool:
        return self.rules.is_session_timeout(session.last_activity)
    
    def end_session(self, session: Session) -> dict:
        
        if not session.is_active():
            return {
                'status': 'already_closed', 
                'emissions_kg': Decimal('0')
            }
        
        session.close()
        emissions_kg = self.calculate_emissions(session)
        
        return {
            'status': 'closed',
            'session_id': session.session_id,
            'user_id': session.user_id,
            'duration_seconds': session.duration_seconds(),
            'event_count': session.event_count(),
            'emissions_kg': emissions_kg
        }
    
    def calculate_emissions(self, session: Session) -> Decimal:
        return self.rules.calculate_session_emissions(
            duration_seconds=session.duration_seconds(),
            event_count=session.event_count()
        )