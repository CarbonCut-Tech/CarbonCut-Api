from typing import Optional
import logging
from domain.base import BaseEventProcessor
from domain.registry import EventProcessorRegistry

logger = logging.getLogger(__name__)

class EventDispatcher:
    def get_processor(self, event_type: str) -> Optional[BaseEventProcessor]:
        processor = EventProcessorRegistry.get_processor(event_type)
        
        if not processor:
            logger.warning(f"No processor found for event type: {event_type}")
        
        return processor
    
    def process_event(self, event_type: str, payload: dict) -> dict:
        processor = self.get_processor(event_type)
        
        if not processor:
            raise ValueError(f"No processor found for event type: {event_type}")
        
        result = processor.process(payload)
        
        return {
            'kg_co2_emitted': result.kg_co2_emitted,
            'reference_id': result.reference_id,
            'reference_type': result.reference_type,
            'metadata': result.metadata
        }
    
    # def list_supported_events(self) -> list:
    #     return EventProcessorRegistry.list_event_types()