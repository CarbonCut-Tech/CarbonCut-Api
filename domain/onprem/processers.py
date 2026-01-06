from decimal import Decimal
from domain.base import BaseEventProcessor, EventProcessingResult
from domain.registry import EventProcessorRegistry
from calculators.onprem_servers import OnPremServerCalculator
from apps.common.event_types import EventTypes
from domain.registry import event_processor

@event_processor(EventTypes.ONPREM_SERVER)
class OnPremServerProcessor(BaseEventProcessor):
    @property
    def event_type(self) -> str:
        return EventTypes.ONPREM_SERVER
    
    def validate_payload(self, payload: dict) -> dict:
        required = ['servers']
        for field in required:
            if field not in payload:
                raise ValueError(f"Missing required field: {field}")
        return payload
    
    def process(self, payload: dict) -> EventProcessingResult:
        calculator = OnPremServerCalculator()
        
        result = calculator.calculate(payload)
        
        reference_id = payload.get('reference_id', f"onprem_{payload.get('month', 'unknown')}")
        
        return EventProcessingResult(
            kg_co2_emitted=Decimal(str(result['total_emissions_kg'])),
            reference_id=reference_id,
            reference_type='onprem_server',
            metadata={
                'server_count': len(payload.get('servers', [])),
                'breakdown': result['breakdown'],
                'factors': result['factors']
            }
        )
EventProcessorRegistry.register(OnPremServerProcessor)