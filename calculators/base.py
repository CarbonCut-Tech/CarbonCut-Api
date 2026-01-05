from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Any
from enum import Enum
from pydantic import BaseModel


class DeviceType(str, Enum):
    MOBILE = 'mobile'
    DESKTOP = 'desktop'
    TABLET = 'tablet'


class EmissionUnit(str, Enum):
    GRAMS = 'g'
    KILOGRAMS = 'kg'
    TONNES = 't'


class CalculationStatus(str, Enum):
    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'

class EmissionResult(BaseModel):
    total_emissions_kg: float
    breakdown: Dict[str, float]
    factors: Dict[str, Any]
    
    class Config:
        frozen = True


class BaseEmissionCalculator(ABC):
    @abstractmethod
    def calculate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    def _to_decimal(self, value: Any) -> Decimal:
        if isinstance(value, Decimal):
            return value
        if value is None:
            return Decimal('0')
        return Decimal(str(value))
    
    def _to_kg(self, grams: Decimal) -> Decimal:
        return grams / Decimal('1000')
    
    def _convert_unit(self, value: Decimal, from_unit: EmissionUnit, to_unit: EmissionUnit) -> Decimal:
        conversions = {
            (EmissionUnit.GRAMS, EmissionUnit.KILOGRAMS): Decimal('0.001'),
            (EmissionUnit.KILOGRAMS, EmissionUnit.GRAMS): Decimal('1000'),
            (EmissionUnit.KILOGRAMS, EmissionUnit.TONNES): Decimal('0.001'),
            (EmissionUnit.TONNES, EmissionUnit.KILOGRAMS): Decimal('1000'),
        }
        
        if from_unit == to_unit:
            return value
        
        factor = conversions.get((from_unit, to_unit))
        if factor:
            return value * factor

        if from_unit != EmissionUnit.KILOGRAMS:
            value = self._convert_unit(value, from_unit, EmissionUnit.KILOGRAMS)
        return self._convert_unit(value, EmissionUnit.KILOGRAMS, to_unit)