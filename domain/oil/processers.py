from decimal import Decimal
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
from domain.base import BaseEventProcessor, EventProcessingResult
from domain.registry import EventProcessorRegistry
from calculators.oil_gas_lubricant import OilGasLubricantCalculator
from apps.common.event_types import EventTypes
from domain.registry import event_processor


class OilEventPayload(BaseModel):
    machine_id: str = Field(..., description="Unique machine identifier")
    run_id: str = Field(..., description="Unique run identifier")
    volume_liters: float = Field(..., gt=0, description="Volume of oil/lubricant used")
    started_at: datetime = Field(..., description="Run start time")
    ended_at: datetime = Field(..., description="Run end time")
    machine_type: str = Field(default="generic", description="Type of machine")
    location: str = Field(default="", description="Location of machine")
    
    fuel_type: Optional[str] = None
    efficiency_rating: Optional[float] = None
    
    class Config:
        extra = 'allow'
    
    @validator('ended_at')
    def validate_end_time(cls, v, values):
        if 'started_at' in values and v < values['started_at']:
            raise ValueError('ended_at must be after started_at')
        return v

@event_processor(EventTypes.OIL_GAS_LUBRICANT)
class OilGasLubricantProcessor(BaseEventProcessor):
    @property
    def event_type(self) -> str:
        return EventTypes.OIL_GAS_LUBRICANT 
    
    def validate_payload(self, payload: dict) -> dict:
        validated = OilEventPayload(**payload)
        return validated.dict()
    
    def process(self, payload: dict) -> EventProcessingResult:
        calculator = OilGasLubricantCalculator()
        
        # Calculate emissions
        result = calculator.calculate({
            'volume_liters': payload['volume_liters']
        })
        
        duration_seconds = (
            payload['ended_at'] - payload['started_at']
        ).total_seconds()
        
        return EventProcessingResult(
            kg_co2_emitted=Decimal(str(result['total_emissions_kg'])),
            reference_id=payload['run_id'],
            reference_type='oil_gas_lubricant_run',
            metadata={
                'machine_id': payload['machine_id'],
                'machine_type': payload['machine_type'],
                'location': payload['location'],
                'volume_liters': payload['volume_liters'],
                'duration_seconds': duration_seconds,
                'fuel_type': payload.get('fuel_type'),
                'efficiency_rating': payload.get('efficiency_rating'),
                'started_at': payload['started_at'].isoformat(),
                'ended_at': payload['ended_at'].isoformat(),
                'breakdown': result['breakdown']
            }
        )

EventProcessorRegistry.register(OilGasLubricantProcessor)