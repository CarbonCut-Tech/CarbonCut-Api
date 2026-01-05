from typing import Optional, List
from datetime import datetime, timedelta
from core.models.session import Session, SessionEvent
import logging

logger = logging.getLogger(__name__)

class SessionData:
    def save(self, session: Session, api_key_id: int):
        from apps.event.models import Session as DjangoSession
        
        events_data = [
            {
                'event_type': e.event_type,
                'timestamp': e.timestamp.isoformat(),
                'page_url': e.page_url,
                'referrer': e.referrer,
                'metadata': e.metadata
            }
            for e in session.events
        ]
        
        DjangoSession.objects.update_or_create(
            session_id=session.session_id,
            user_id=session.user_id,
            defaults={
                'started_at': session.started_at,
                'last_activity': session.last_activity,
                'status': session.status,
                'device_type': session.device_type,
                'country': session.country,
                'campaign_id': session.campaign_id,
                'user_agent': session.user_agent,
                'ip_address': session.ip_address,
                'events_data': events_data,
            }
        )
    
    def get_active_session(self, session_id: str, user_id: str) -> Optional[Session]:
        from apps.event.models import Session as DjangoSession
        
        try:
            orm_session = DjangoSession.objects.get(
                session_id=session_id,
                user_id=user_id,
                status='active'
            )
            
            return self._to_domain(orm_session)
            
        except DjangoSession.DoesNotExist:
            return None
    
    def get_inactive_sessions(self, timeout_seconds: int) -> List[Session]:
        from apps.event.models import Session as DjangoSession
        
        cutoff_time = datetime.now() - timedelta(seconds=timeout_seconds)
        
        orm_sessions = DjangoSession.objects.filter(
            status='active',
            last_activity__lt=cutoff_time
        )
        
        return [self._to_domain(s) for s in orm_sessions]
    
    def _to_domain(self, orm_session) -> Session:
        from dateutil import parser
        
        events = [
            SessionEvent(
                event_type=e['event_type'],
                timestamp=parser.parse(e['timestamp']),
                page_url=e.get('page_url', ''),
                referrer=e.get('referrer', ''),
                metadata=e.get('metadata', {})
            )
            for e in (orm_session.events_data or [])
        ]
        
        return Session(
            session_id=orm_session.session_id,
            user_id=orm_session.user_id,
            started_at=orm_session.started_at,
            last_activity=orm_session.last_activity,
            events=events,
            status=orm_session.status,
            device_type=orm_session.device_type,
            country=orm_session.country,
            campaign_id=orm_session.campaign_id,
            user_agent=orm_session.user_agent,
            ip_address=orm_session.ip_address or '',
        )