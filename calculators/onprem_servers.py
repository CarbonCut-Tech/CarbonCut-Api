from decimal import Decimal
from typing import Dict, Any, List
from .base import BaseEmissionCalculator
from constants.emission_factors import (
    get_grid_factor,
    SERVER_TDP_FACTORS,
    PUE_DEFAULTS
)

class OnPremServerCalculator(BaseEmissionCalculator):
    def calculate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Input:
        - servers: List of server specs
        - location_country_code: For grid factor
        - pue: Power Usage Effectiveness (default 1.6)
        - calculation_period: 'monthly' or 'annual'
        """
        servers = input_data.get('servers', [])
        location_country_code = input_data.get('location_country_code', 'WORLD').upper()
        pue = self._to_decimal(input_data.get('pue', PUE_DEFAULTS['default']))
        calculation_period = input_data.get('calculation_period', 'monthly')
        
        total_emissions_kg = Decimal('0')
        server_details = []
        
        for server in servers:
            server_result = self._calculate_single_server(
                server,
                location_country_code,
                pue,
                calculation_period
            )
            total_emissions_kg += server_result['emissions_kg']
            server_details.append(server_result)
        
        return {
            'total_emissions_kg': float(total_emissions_kg),
            'total_emissions_g': float(total_emissions_kg * 1000),
            'breakdown': {
                'server_count': len(servers),
                'servers': server_details,
                'total_energy_kwh': sum(s['energy_kwh'] for s in server_details)
            },
            'factors': {
                'location_country_code': location_country_code,
                'pue': float(pue),
                'calculation_period': calculation_period,
                'version': self.VERSION
            }
        }
    
    def _calculate_single_server(
        self,
        server: Dict[str, Any],
        location_country_code: str,
        pue: Decimal,
        calculation_period: str
    ) -> Dict[str, Any]:
        cpu_cores = self._to_decimal(server.get('cpu_cores', 0))
        ram_gb = self._to_decimal(server.get('ram_gb', 0))
        storage_tb = self._to_decimal(server.get('storage_tb', 0))
        storage_type = server.get('storage_type', 'hdd').lower()
        avg_cpu_utilization = self._to_decimal(server.get('avg_cpu_utilization', 0.5))
        hours_per_day = self._to_decimal(server.get('hours_per_day', 24))
        days_per_month = self._to_decimal(server.get('days_per_month', 30))
        
        cpu_tdp_watts = cpu_cores * SERVER_TDP_FACTORS['cpu_watts_per_core']
        ram_tdp_watts = ram_gb * SERVER_TDP_FACTORS['ram_watts_per_gb']
        
        if storage_type == 'ssd':
            storage_tdp_watts = storage_tb * SERVER_TDP_FACTORS['storage_ssd_watts_per_tb']
        elif storage_type == 'nvme':
            storage_tdp_watts = storage_tb * SERVER_TDP_FACTORS['storage_nvme_watts_per_tb']
        else:  # hdd
            storage_tdp_watts = storage_tb * SERVER_TDP_FACTORS['storage_hdd_watts_per_tb']
        
        network_watts = SERVER_TDP_FACTORS['network_base_watts']
        
        total_tdp_watts = cpu_tdp_watts + ram_tdp_watts + storage_tdp_watts + network_watts

        actual_power_watts = total_tdp_watts * avg_cpu_utilization

        if calculation_period == 'monthly':
            total_hours = hours_per_day * days_per_month
        else:  # annual
            total_hours = hours_per_day * Decimal('365')
        
        energy_kwh = (actual_power_watts * total_hours * pue) / Decimal('1000')
        
        grid_factor_kg = get_grid_factor(location_country_code) / Decimal('1000')
        emissions_kg = energy_kwh * grid_factor_kg
        
        return {
            'server_name': server.get('name', 'Unnamed Server'),
            'cpu_cores': int(cpu_cores),
            'ram_gb': int(ram_gb),
            'storage_tb': float(storage_tb),
            'tdp_breakdown': {
                'cpu_watts': float(cpu_tdp_watts),
                'ram_watts': float(ram_tdp_watts),
                'storage_watts': float(storage_tdp_watts),
                'network_watts': float(network_watts),
                'total_tdp_watts': float(total_tdp_watts)
            },
            'actual_power_watts': float(actual_power_watts),
            'energy_kwh': float(energy_kwh),
            'emissions_kg': float(emissions_kg),
            'utilization': float(avg_cpu_utilization)
        }