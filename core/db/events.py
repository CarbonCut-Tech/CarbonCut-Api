from typing import Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from core.models.event import ProcessedEvent, ActiveSession
import logging
from django.db import models

logger = logging.getLogger(__name__)


class ProcessedEventData:
    def is_processed(self, reference_id: str, reference_type: str) -> bool:
        from apps.event.models import ProcessedEvent as DjangoProcessedEvent
        
        return DjangoProcessedEvent.objects.filter(
            reference_id=reference_id,
            reference_type=reference_type
        ).exists()
    
    def mark_processed(
        self,
        reference_id: str,
        reference_type: str,
        user_id: str,
        event_type: str,
        kg_co2_emitted: Decimal,
        metadata: dict = None
    ) -> ProcessedEvent:
        from apps.event.models import ProcessedEvent as DjangoProcessedEvent
        
        orm_event, created = DjangoProcessedEvent.objects.get_or_create(
            reference_id=reference_id,
            reference_type=reference_type,
            defaults={
                'user_id': user_id,
                'event_type': event_type,
                'kg_co2_emitted': kg_co2_emitted,
                'processed_at': datetime.now(),
                'metadata': metadata or {}
            }
        )
        
        if not created:
            logger.warning(
                f"Event already processed: {reference_type}:{reference_id}"
            )
        
        return self._to_domain(orm_event)
    
    def get_processed_events(
        self,
        user_id: str,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[ProcessedEvent]:
        from apps.event.models import ProcessedEvent as DjangoProcessedEvent
        
        queryset = DjangoProcessedEvent.objects.filter(user_id=user_id)
        
        if since:
            queryset = queryset.filter(processed_at__gte=since)
        
        orm_events = queryset.order_by('-processed_at')[:limit]
        
        return [self._to_domain(e) for e in orm_events]
    
    def _to_domain(self, orm_event) -> ProcessedEvent:
        return ProcessedEvent(
            reference_id=orm_event.reference_id,
            reference_type=orm_event.reference_type,
            user_id=orm_event.user_id,
            event_type=orm_event.event_type,
            kg_co2_emitted=orm_event.kg_co2_emitted,
            processed_at=orm_event.processed_at,
            metadata=orm_event.metadata or {}
        )


class ActiveSessionData:
    def get_or_create(
        self,
        session_id: str,
        user_id: str,
        api_key: str
    ) -> ActiveSession:
        """Get or create active session"""
        from apps.event.models import ActiveSession as DjangoActiveSession
        from django.utils import timezone
        
        orm_session, created = DjangoActiveSession.objects.get_or_create(
            session_id=session_id,
            defaults={
                'user_id': user_id,
                'api_key': api_key,
                'last_event_at': timezone.now(),
                'event_count': 0,
                'status': 'active'
            }
        )
        
        return self._to_domain(orm_session)
    
    def update_activity(self, session_id: str) -> ActiveSession:
        from apps.event.models import ActiveSession as DjangoActiveSession
        from django.utils import timezone
        
        orm_session = DjangoActiveSession.objects.get(session_id=session_id)
        orm_session.last_event_at = timezone.now()
        orm_session.event_count += 1
        orm_session.save(update_fields=['last_event_at', 'event_count'])
        
        return self._to_domain(orm_session)
    
    def mark_processed(self, session_id: str):
        from apps.event.models import ActiveSession as DjangoActiveSession
        from django.utils import timezone
        
        DjangoActiveSession.objects.filter(session_id=session_id).update(
            last_processed_at=timezone.now()
        )
    
    def get_active_sessions(self, inactive_threshold_minutes: int = 5) -> List[ActiveSession]:
        from apps.event.models import ActiveSession as DjangoActiveSession
        from django.utils import timezone
        
        threshold = timezone.now() - timedelta(minutes=inactive_threshold_minutes)
        orm_sessions = DjangoActiveSession.objects.filter(
            status='active'
        ).filter(
            models.Q(last_processed_at__isnull=True) |
            models.Q(last_processed_at__lt=threshold)
        )
        
        return [self._to_domain(s) for s in orm_sessions]
    
    def get_inactive_sessions(self, timeout_minutes: int = 30) -> List[ActiveSession]:
        from apps.event.models import ActiveSession as DjangoActiveSession
        from django.utils import timezone
        
        cutoff = timezone.now() - timedelta(minutes=timeout_minutes)
        
        orm_sessions = DjangoActiveSession.objects.filter(
            status='active',
            last_event_at__lt=cutoff
        )
        
        return [self._to_domain(s) for s in orm_sessions]
    
    def mark_inactive(self, session_id: str):
        from apps.event.models import ActiveSession as DjangoActiveSession
        
        DjangoActiveSession.objects.filter(session_id=session_id).update(
            status='inactive'
        )
        
        logger.info(f"Session marked inactive: {session_id}")
    
    def mark_closed(self, session_id: str):
        from apps.event.models import ActiveSession as DjangoActiveSession
        
        DjangoActiveSession.objects.filter(session_id=session_id).update(
            status='closed'
        )
        
        logger.info(f"Session closed: {session_id}")
    
    def _to_domain(self, orm_session) -> ActiveSession:
        return ActiveSession(
            session_id=orm_session.session_id,
            user_id=orm_session.user_id,
            api_key=orm_session.api_key,
            last_event_at=orm_session.last_event_at,
            event_count=orm_session.event_count,
            status=orm_session.status,
            created_at=orm_session.created_at,
            last_processed_at=orm_session.last_processed_at
        )