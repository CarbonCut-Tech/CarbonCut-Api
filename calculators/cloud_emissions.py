from decimal import Decimal
from typing import Dict, Any, List
from .base import BaseEmissionCalculator
from constants.emission_factors import (
    get_grid_factor,
    get_cloud_cost_factor,
    GRID_INTENSITY_G_PER_KWH
)

class CloudEmissionsCalculator(BaseEmissionCalculator):
    """
        Calculate cloud emissions
        
        Input options:
        - csv_data: List of dicts with service, region, usage, emissions
        - monthly_cost_usd: For cost-based estimation
        - provider: aws, gcp, azure
        - region: Cloud region
    """
    def calculate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        provider = input_data.get('provider', 'aws').lower()
        calculation_method = input_data.get('calculation_method', 'csv')
        
        if calculation_method == 'csv' and 'csv_data' in input_data:
            return self._calculate_from_csv(input_data['csv_data'], provider)
        elif calculation_method == 'cost' and 'monthly_cost_usd' in input_data:
            return self._calculate_from_cost(
                input_data['monthly_cost_usd'],
                provider,
                input_data.get('region', 'default')
            )
        else:
            raise ValueError("Invalid calculation method or missing data")
    
    def _calculate_from_csv(
        self,
        csv_data: List[Dict[str, Any]],
        provider: str
    ) -> Dict[str, Any]:
        total_emissions_kg = Decimal('0')
        service_breakdown = {}
        region_breakdown = {}
        
        for row in csv_data:
            service = row.get('service', 'unknown')
            region = row.get('region', 'unknown')
            emissions_kg = self._to_decimal(row.get('emissions_kg_co2', 0))
            
            total_emissions_kg += emissions_kg

            if service not in service_breakdown:
                service_breakdown[service] = Decimal('0')
            service_breakdown[service] += emissions_kg

            if region not in region_breakdown:
                region_breakdown[region] = Decimal('0')
            region_breakdown[region] += emissions_kg
        
        return {
            'total_emissions_kg': float(total_emissions_kg),
            'total_emissions_g': float(total_emissions_kg * 1000),
            'breakdown': {
                'by_service': {k: float(v) for k, v in service_breakdown.items()},
                'by_region': {k: float(v) for k, v in region_breakdown.items()}
            },
            'factors': {
                'provider': provider,
                'calculation_method': 'csv_data',
                'accuracy': 'high',
                'version': self.VERSION
            }
        }
    
    def _calculate_from_cost(
        self,
        monthly_cost_usd: float,
        provider: str,
        region: str
    ) -> Dict[str, Any]:
        cost = self._to_decimal(monthly_cost_usd)
        emission_factor = get_cloud_cost_factor(provider, region)
        
        total_emissions_kg = cost * emission_factor
        
        return {
            'total_emissions_kg': float(total_emissions_kg),
            'total_emissions_g': float(total_emissions_kg * 1000),
            'breakdown': {
                'monthly_cost_usd': float(cost),
                'emission_factor_kg_per_usd': float(emission_factor)
            },
            'factors': {
                'provider': provider,
                'region': region,
                'calculation_method': 'cost_estimate',
                'accuracy': 'medium',
                'version': self.VERSION,
                'note': 'Estimation based on cost. Upload CSV for accurate data.'
            }
        }