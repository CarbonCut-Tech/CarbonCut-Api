from decimal import Decimal
from typing import Dict, Any
from .base import BaseEmissionCalculator
from constants.emission_factors import (
    get_grid_factor,
    get_cdn_efficiency,
)
class CDNDataTransferCalculator(BaseEmissionCalculator):
    DEFAULT_CDN_PUE = Decimal('1.2')
    def calculate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Input:
        - monthly_gb_transferred: GB transferred per month
        - provider: CDN provider (cloudflare, aws_cloudfront, etc.)
        - regions: List of regions or single region
        """        
        monthly_gb = self._to_decimal(input_data.get('monthly_gb_transferred', 0))
        provider = input_data.get('provider', 'generic').lower()
        regions = input_data.get('regions', ['WORLD'])

        kwh_per_gb = get_cdn_efficiency(provider)
        energy_kwh = monthly_gb * kwh_per_gb * self.DEFAULT_CDN_PUE

        if isinstance(regions, list) and len(regions) > 1:
            grid_factors = [get_grid_factor(region) for region in regions]
            avg_grid_factor_g = sum(grid_factors) / len(grid_factors)
            grid_factor_kg = avg_grid_factor_g / Decimal('1000')
        else:
            region = regions[0] if isinstance(regions, list) else regions
            grid_factor_kg = get_grid_factor(region) / Decimal('1000')
        
        emissions_kg = energy_kwh * grid_factor_kg
        
        return {
            'total_emissions_kg': float(emissions_kg),
            'total_emissions_g': float(emissions_kg * 1000),
            'breakdown': {
                'monthly_gb_transferred': float(monthly_gb),
                'energy_kwh': float(energy_kwh),
                'kwh_per_gb': float(kwh_per_gb),
                'pue': float(self.DEFAULT_CDN_PUE)
            },
            'factors': {
                'provider': provider,
                'regions': regions,
                'grid_factor_kg_per_kwh': float(grid_factor_kg),
                'cdn_efficiency_kwh_per_gb': float(kwh_per_gb),
                'version': self.VERSION
            }
        }