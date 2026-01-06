from typing import Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from core.models.event import ProcessedEvent, ActiveSession
from django.db import IntegrityError, transaction
import logging

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
    ) -> tuple[ProcessedEvent, bool]:
        from apps.event.models import ProcessedEvent as DjangoProcessedEvent
        
        try:
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
                logger.info(
                    f"Event already processed (idempotent): {reference_type}:{reference_id}"
                )
            return self._to_domain(orm_event), created
        except IntegrityError as e:
            logger.warning(
                f"processing for {reference_type}:{reference_id}"
            )
            orm_event = DjangoProcessedEvent.objects.get(
                reference_id=reference_id,
                reference_type=reference_type
            )
            return self._to_domain(orm_event), False
    
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
    
    def update_activity(
        self,
        session_id: str,
    ) -> None:
        from apps.event.models import ActiveSession as DjangoActiveSession
        from django.utils import timezone
        from django.db.models import F
        
        DjangoActiveSession.objects.filter(
            session_id=session_id
        ).update(
            last_event_at=timezone.now(),
            event_count=F('event_count') + 1
        )
    
    def get_active_sessions(
        self,
        timeout_minutes: int = 30
    ) -> List[ActiveSession]:
        from apps.event.models import ActiveSession as DjangoActiveSession
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_time = timezone.now() - timedelta(minutes=timeout_minutes)
        
        orm_sessions = DjangoActiveSession.objects.filter(
            status='active',
            last_event_at__gte=cutoff_time
        )
        
        return [self._to_domain(s) for s in orm_sessions]
    
    def mark_processed(
        self,
        session_id: str,
        processed_at: datetime
    ) -> None:
        from apps.event.models import ActiveSession as DjangoActiveSession
        
        DjangoActiveSession.objects.filter(
            session_id=session_id
        ).update(
            last_processed_at=processed_at
        )
    
    def close_session(
        self,
        session_id: str
    ) -> None:
        from apps.event.models import ActiveSession as DjangoActiveSession
        
        DjangoActiveSession.objects.filter(
            session_id=session_id
        ).update(
            status='closed'
        )
    
    def _to_domain(self, orm_session) -> ActiveSession:
        return ActiveSession(
            session_id=orm_session.session_id,
            user_id=orm_session.user_id,
            api_key=orm_session.api_key,
            last_event_at=orm_session.last_event_at,
            event_count=orm_session.event_count,
            status=orm_session.status,
            last_processed_at=orm_session.last_processed_at,
        )