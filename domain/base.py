from abc import ABC, abstractmethod
from typing import Dict, Any
from decimal import Decimal
from pydantic import BaseModel

class EventProcessingResult(BaseModel):
    kg_co2_emitted: Decimal
    reference_id: str
    reference_type: str
    metadata: Dict[str, Any] = {}
    
    class Config:
        arbitrary_types_allowed = True

class BaseEventProcessor(ABC):
    @property
    @abstractmethod
    def event_type(self) -> str:
        pass
    
    @abstractmethod
    def validate_payload(self, payload: dict) -> dict:
        pass
    
    @abstractmethod
    def process(self, payload: dict) -> EventProcessingResult:
        pass