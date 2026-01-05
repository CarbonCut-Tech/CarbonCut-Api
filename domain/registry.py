from typing import Dict, Type, Optional
from .base import BaseEventProcessor
import logging

logger = logging.getLogger(__name__)

class EventProcessorRegistry:
    _processors: Dict[str, Type[BaseEventProcessor]] = {}
    
    @classmethod
    def register(cls, processor_class: Type[BaseEventProcessor]):
        instance = processor_class()
        cls._processors[instance.event_type] = processor_class
        logger.info(f"Registered event processor: {instance.event_type}")
    
    @classmethod
    def get_processor(cls, event_type: str) -> Optional[BaseEventProcessor]:
        processor_class = cls._processors.get(event_type)
        if processor_class:
            return processor_class()
        return None
    
    @classmethod
    def list_event_types(cls) -> list:
        return list(cls._processors.keys())
    
    @classmethod
    def is_registered(cls, event_type: str) -> bool:
        return event_type in cls._processors