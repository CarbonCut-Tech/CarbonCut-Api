from typing import Optional
import logging
from domain.base import BaseEventProcessor, EventProcessingResult
from domain.registry import EventProcessorRegistry

logger = logging.getLogger(__name__)
class EventDispatcher:
    def get_processor(self, event_type: str) -> Optional[BaseEventProcessor]:
        processor = EventProcessorRegistry.get_processor(event_type)
        
        if not processor:
            logger.warning(f"No processor found for event type: {event_type}")
        
        return processor
    
    def process_event(self, event_type: str, payload: dict) -> EventProcessingResult:
        processor = self.get_processor(event_type)
        
        if not processor:
            raise ValueError(f"No processor found for event type: {event_type}")
        
        return processor.process(payload)  
    
    # def list_supported_events(self) -> list:
    #     return EventProcessorRegistry.list_event_types()