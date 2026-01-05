from typing import List, Dict, Any
import uuid
import logging
from core.db.events import ActiveSessionData
from datetime import datetime

logger = logging.getLogger(__name__)

class EventQueueService:
    def __init__(self):
        self.active_sessions = ActiveSessionData()
    
    def queue_event(
        self,
        user_id: str,
        event_type: str,
        payload: dict,
        api_key: str
    ) -> dict:
        session_id = payload.get('session_id')
        if session_id:
            self.active_sessions.get_or_create(session_id, user_id, api_key)
            self.active_sessions.update_activity(session_id)
        
        batch_id = str(uuid.uuid4())
        
        event = {
            'event_type': event_type,
            'payload': payload,
            'user_id': user_id,
            'api_key': api_key,
            'queued_at': datetime.now().isoformat()
        }
        
        from core.tasks import process_event_batch_task
        process_event_batch_task.delay([event])
        
        logger.info(f"Queued single event {event_type} for user {user_id} to Celery/SQS")
        
        return {
            'batch_id': batch_id,
            'events': [event],
            'queued': True
        }
    
    def queue_events_batch(
        self,
        user_id: str,
        events: List[Dict[str, Any]],
        api_key: str
    ) -> dict:
        batch_id = str(uuid.uuid4())
        
        for event in events:
            session_id = event.get('payload', {}).get('session_id')
            if session_id:
                self.active_sessions.get_or_create(session_id, user_id, api_key)
                self.active_sessions.update_activity(session_id)
        
        for event in events:
            event['queued_at'] = datetime.now().isoformat()
        
        from core.tasks import process_event_batch_task
        process_event_batch_task.delay(events)
        
        logger.info(f"Queued batch {batch_id} with {len(events)} events to Celery/SQS")
        
        return {
            'batch_id': batch_id,
            'events': events,
            'event_count': len(events),
            'queued': True
        }