import logging

logger = logging.getLogger(__name__)


class EventValidationError(Exception):
    pass


class EventValidationService:
    REQUIRED_FIELDS = ['api_key', 'session_id', 'event_type', 'event_time']
    
    @staticmethod
    def validate(event_data: dict) -> None:
        missing_fields = [
            field for field in EventValidationService.REQUIRED_FIELDS 
            if not event_data.get(field)
        ]
        
        if missing_fields:
            raise EventValidationError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        logger.info(f"Event validation passed for {event_data.get('event_type')}")