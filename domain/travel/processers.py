from decimal import Decimal
from domain.base import BaseEventProcessor, EventProcessingResult
from domain.registry import EventProcessorRegistry
from calculators.travel_emissions import TravelEmissionsCalculator
from apps.common.event_types import EventTypes
from domain.registry import event_processor

@event_processor(EventTypes.TRAVEL_EMISSIONS)
class TravelEmissionsProcessor(BaseEventProcessor):    
    @property
    def event_type(self) -> str:
        return EventTypes.TRAVEL_EMISSIONS
    
    def validate_payload(self, payload: dict) -> dict:
        required = ['travel_type']
        for field in required:
            if field not in payload:
                raise ValueError(f"Missing required field: {field}")
        return payload
    
    def process(self, payload: dict) -> EventProcessingResult:
        calculator = TravelEmissionsCalculator()
        
        result = calculator.calculate(payload)
        
        travel_type = payload.get('travel_type')
        reference_id = payload.get('reference_id', f"travel_{travel_type}_{payload.get('date', 'unknown')}")
        
        return EventProcessingResult(
            kg_co2_emitted=Decimal(str(result['total_emissions_kg'])),
            reference_id=reference_id,
            reference_type=f'travel_{travel_type}',
            metadata={
                'travel_type': travel_type,
                'breakdown': result['breakdown'],
                'factors': result['factors']
            }
        )
EventProcessorRegistry.register(TravelEmissionsProcessor)