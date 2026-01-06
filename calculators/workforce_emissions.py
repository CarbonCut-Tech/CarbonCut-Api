from decimal import Decimal
from typing import Dict, Any, List
from .base import BaseEmissionCalculator
from constants.emission_factors import (
    get_grid_factor,
    WORKFORCE_ENERGY_CONSTANTS
)


class WorkforceEmissionsCalculator(BaseEmissionCalculator):
    """
        Calculate workforce emissions
        Input:
        - total_employees: Total employee count
        - remote_percentage: 0-100
        - office_locations: List of offices with sqm and country_code
        - calculation_period: 'monthly' or 'annual'
    """
    VERSION = "2026.1"
    def calculate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        total_employees = self._to_decimal(input_data.get('total_employees', 0))
        remote_percentage = self._to_decimal(input_data.get('remote_percentage', 0)) / 100
        office_locations = input_data.get('office_locations', [])
        calculation_period = input_data.get('calculation_period', 'monthly')
        
        remote_emissions = self._calculate_remote_work(
            total_employees,
            remote_percentage,
            calculation_period
        )
        
        office_emissions = self._calculate_office_energy(
            office_locations,
            calculation_period
        )
        
        total_emissions_kg = remote_emissions['emissions_kg'] + office_emissions['emissions_kg']
        
        return {
            'total_emissions_kg': float(total_emissions_kg),
            'total_emissions_g': float(total_emissions_kg * 1000),
            'breakdown': {
                'remote_work_kg': float(remote_emissions['emissions_kg']),
                'office_energy_kg': float(office_emissions['emissions_kg']),
                'remote_work_details': remote_emissions['details'],
                'office_energy_details': office_emissions['details']
            },
            'factors': {
                'calculation_period': calculation_period,
                'version': self.VERSION
            }
        }
    
    def _calculate_remote_work(
        self,
        total_employees: Decimal,
        remote_percentage: Decimal,
        calculation_period: str
    ) -> Dict[str, Any]:
        remote_employees = total_employees * remote_percentage
        energy_per_day_kwh = WORKFORCE_ENERGY_CONSTANTS['remote_home_energy_kwh_per_day']

        if calculation_period == 'monthly':
            working_days = WORKFORCE_ENERGY_CONSTANTS['working_days_per_month']
        else:  # annual
            working_days = WORKFORCE_ENERGY_CONSTANTS['working_days_per_year']
        
        total_energy_kwh = remote_employees * energy_per_day_kwh * working_days
        
        grid_factor_kg = get_grid_factor('WORLD') / Decimal('1000')
        
        emissions_kg = total_energy_kwh * grid_factor_kg
        
        return {
            'emissions_kg': emissions_kg,
            'details': {
                'remote_employees': float(remote_employees),
                'energy_per_day_kwh': float(energy_per_day_kwh),
                'working_days': int(working_days),
                'total_energy_kwh': float(total_energy_kwh),
                'grid_factor_kg_per_kwh': float(grid_factor_kg)
            }
        }
    
    def _calculate_office_energy(
        self,
        office_locations: List[Dict[str, Any]],
        calculation_period: str
    ) -> Dict[str, Any]:
        total_emissions_kg = Decimal('0')
        office_details = []
        
        for office in office_locations:
            square_meters = self._to_decimal(office.get('square_meters', 0))
            country_code = office.get('country_code', 'WORLD').upper()

            annual_energy_per_sqm = WORKFORCE_ENERGY_CONSTANTS['office_energy_kwh_per_sqm_per_year']
            
            if calculation_period == 'monthly':
                period_energy_per_sqm = annual_energy_per_sqm / 12
            else:  # annual
                period_energy_per_sqm = annual_energy_per_sqm
            
            office_energy_kwh = square_meters * period_energy_per_sqm
            
            grid_factor_kg = get_grid_factor(country_code) / Decimal('1000')

            office_emissions_kg = office_energy_kwh * grid_factor_kg
            total_emissions_kg += office_emissions_kg
            
            office_details.append({
                'city': office.get('city', 'Unknown'),
                'country_code': country_code,
                'square_meters': float(square_meters),
                'energy_kwh': float(office_energy_kwh),
                'emissions_kg': float(office_emissions_kg),
                'grid_factor_kg_per_kwh': float(grid_factor_kg)
            })
        
        return {
            'emissions_kg': total_emissions_kg,
            'details': {
                'office_count': len(office_locations),
                'offices': office_details
            }
        }