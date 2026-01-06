from decimal import Decimal
from domain.base import BaseEventProcessor, EventProcessingResult
from domain.registry import EventProcessorRegistry
from calculators.workforce_emissions import WorkforceEmissionsCalculator
from apps.common.event_types import EventTypes
from domain.registry import event_processor

@event_processor(EventTypes.WORKFORCE_EMISSIONS)
class WorkforceEmissionsProcessor(BaseEventProcessor):
    @property
    def event_type(self) -> str:
        return EventTypes.WORKFORCE_EMISSIONS
    
    def validate_payload(self, payload: dict) -> dict:
        required = ['total_employees']
        for field in required:
            if field not in payload:
                raise ValueError(f"Missing required field: {field}")
        return payload
    
    def process(self, payload: dict) -> EventProcessingResult:
        calculator = WorkforceEmissionsCalculator()
        
        result = calculator.calculate(payload)
        
        reference_id = payload.get('reference_id', f"workforce_{payload.get('month', 'unknown')}")
        
        return EventProcessingResult(
            kg_co2_emitted=Decimal(str(result['total_emissions_kg'])),
            reference_id=reference_id,
            reference_type='workforce',
            metadata={
                'total_employees': payload.get('total_employees'),
                'remote_percentage': payload.get('remote_percentage'),
                'breakdown': result['breakdown'],
                'factors': result['factors']
            }
        )
EventProcessorRegistry.register(WorkforceEmissionsProcessor)