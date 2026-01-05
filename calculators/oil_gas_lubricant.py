from decimal import Decimal
from typing import Dict, Any
from .base import BaseEmissionCalculator


class OilGasLubricantCalculator(BaseEmissionCalculator):
    
    EMISSION_FACTOR_KG_CO2_PER_LITER = Decimal('2.68')
    PRODUCTION_EMISSION_FACTOR = Decimal('0.42')
    TRANSPORT_EMISSION_FACTOR = Decimal('0.15')
    
    def calculate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        volume_liters = self._to_decimal(input_data.get('volume_liters', 0))
        production_factor = self._to_decimal(
            input_data.get('production_factor', self.PRODUCTION_EMISSION_FACTOR)
        )
        transport_factor = self._to_decimal(
            input_data.get('transport_factor', self.TRANSPORT_EMISSION_FACTOR)
        )
        
        combustion_emissions_kg = volume_liters * self.EMISSION_FACTOR_KG_CO2_PER_LITER
        production_emissions_kg = volume_liters * production_factor
        transport_emissions_kg = volume_liters * transport_factor
        
        total_emissions_kg = combustion_emissions_kg + production_emissions_kg + transport_emissions_kg
        total_emissions_g = total_emissions_kg * Decimal('1000')
        
        return {
            'total_emissions_g': float(total_emissions_g),
            'total_emissions_kg': float(total_emissions_kg),
            'breakdown': {
                'combustion_emissions_kg': float(combustion_emissions_kg),
                'production_emissions_kg': float(production_emissions_kg),
                'transport_emissions_kg': float(transport_emissions_kg),
            },
            'factors': {
                'volume_liters': float(volume_liters),
                'emission_factor_per_liter': float(self.EMISSION_FACTOR_KG_CO2_PER_LITER),
                'production_factor': float(production_factor),
                'transport_factor': float(transport_factor),
            }
        }