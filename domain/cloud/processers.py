from decimal import Decimal
from typing import Dict, Any
from domain.base import BaseEventProcessor, EventProcessingResult
from domain.registry import EventProcessorRegistry
from calculators.cloud_emissions import CloudEmissionsCalculator
from apps.common.event_types import EventTypes
from domain.registry import event_processor

@event_processor(EventTypes.CLOUD_EMISSIONS)
class CloudEmissionsProcessor(BaseEventProcessor):
    @property
    def event_type(self) -> str:
        return EventTypes.CLOUD_EMISSIONS
    
    def validate_payload(self, payload: dict) -> dict:
        required = ['provider', 'calculation_method']
        for field in required:
            if field not in payload:
                raise ValueError(f"Missing required field: {field}")
        return payload
    
    def process(self, payload: dict) -> EventProcessingResult:
        calculator = CloudEmissionsCalculator()
        
        result = calculator.calculate(payload)
        
        provider = payload.get('provider', 'unknown')
        reference_id = payload.get('reference_id', f"cloud_{provider}_{payload.get('month', 'unknown')}")
        
        return EventProcessingResult(
            kg_co2_emitted=Decimal(str(result['total_emissions_kg'])),
            reference_id=reference_id,
            reference_type=f'cloud_{provider}',
            metadata={
                'provider': provider,
                'calculation_method': payload.get('calculation_method'),
                'breakdown': result['breakdown'],
                'factors': result['factors'],
                'accuracy': result['factors'].get('accuracy', 'estimated')
            }
        )
EventProcessorRegistry.register(CloudEmissionsProcessor)