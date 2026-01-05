from decimal import Decimal
from typing import Dict, Any
from .base import BaseEmissionCalculator


class InternetWebsiteCalculator(BaseEmissionCalculator):
    VERSION = "2025.1"

    GRID_INTENSITY_DEFAULTS = {
        'GB': Decimal('233'),
        'US': Decimal('417'),
        'DE': Decimal('385'),
        'FR': Decimal('57'),
        'EU': Decimal('295'),
        'WORLD': Decimal('475'),
    }

    def calculate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        bytes_transferred = self._to_decimal(input_data.get('bytes_transferred', 0))
        region = input_data.get('country_code', 'WORLD').upper()
        grid_ef_kg_per_kwh = self._get_grid_emission_factor(region)

        data_gb = bytes_transferred / Decimal('1073741824')
        energy_use_kwh = data_gb * Decimal('0.5')
        total_energy_kwh = energy_use_kwh * Decimal('1.2')
        emissions_kg = total_energy_kwh * grid_ef_kg_per_kwh

        return {
            'total_emissions_kg': float(emissions_kg),
            'total_emissions_g': float(emissions_kg * Decimal('1000')),
            'breakdown': {
                'data_gb': float(data_gb),
                'energy_use_kwh': float(energy_use_kwh),
                'total_energy_kwh': float(total_energy_kwh),
            },
            'factors': {
                'grid_ef_kg_per_kwh': float(grid_ef_kg_per_kwh),
                'region': region,
            }
        }

    def _get_grid_emission_factor(self, region: str) -> Decimal:
        grid_intensity_g = self.GRID_INTENSITY_DEFAULTS.get(
            region, self.GRID_INTENSITY_DEFAULTS['WORLD']
        )
        return grid_intensity_g / Decimal('1000')