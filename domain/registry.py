from typing import Type, Dict
from domain.base import BaseEventProcessor
import logging

logger = logging.getLogger(__name__)
def event_processor(event_type: str):
    def decorator(cls: Type[BaseEventProcessor]):
        EventProcessorRegistry.register(cls)
        logger.info(f"Registered event processor: {event_type} -> {cls.__name__}")
        return cls
    return decorator

class EventProcessorRegistry:
    _processors: Dict[str, BaseEventProcessor] = {}
    @classmethod
    def register(cls, processor_class: Type[BaseEventProcessor]):
        processor = processor_class()
        event_type = processor.event_type
        
        if event_type in cls._processors:
            logger.warning(f"Overwriting processor for {event_type}")
        
        cls._processors[event_type] = processor
    @classmethod
    def get_processor(cls, event_type: str) -> BaseEventProcessor:
        return cls._processors.get(event_type)