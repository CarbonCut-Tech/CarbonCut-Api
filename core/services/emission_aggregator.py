from typing import Dict, Any, List
from datetime import date, datetime
from decimal import Decimal
from core.models.emission_config import UserEmissionProfile
from core.db.emission_sources import (
    UserEmissionProfileData,
    EmissionSourceData
)
from core.services.event_dispatcher import EventDispatcher
import logging

logger = logging.getLogger(__name__)


class EmissionAggregator:
    def __init__(self):
        self.profile_data = UserEmissionProfileData()
        self.emission_data = EmissionSourceData()
        self.dispatcher = EventDispatcher()
    
    def calculate_monthly_emissions(
        self,
        user_id: str,
        month: int,
        year: int
    ) -> Dict[str, Any]:
        """
        Calculate total emissions for a user for a given month
        
        This processes:
        1. Cloud provider data (if configured)
        2. CDN data (if configured)
        3. Workforce emissions (if configured)
        4. On-prem servers (if configured)
        5. Website SDK data (from existing tracking)
        """
        
        logger.info(f"Calculating monthly emissions for user {user_id}: {year}-{month:02d}")
        
        profile = self.profile_data.get_profile(user_id)
        
        if not profile:
            logger.warning(f"No emission profile found for user {user_id}")
            return {
                'total_kg': 0,
                'by_scope': {},
                'by_source': {},
                'message': 'No emission sources configured'
            }
        
        total_emissions = Decimal('0')
        emissions_by_source = {}
        emissions_by_scope = {
            'scope_1': Decimal('0'),
            'scope_2': Decimal('0'),
            'scope_3': Decimal('0')
        }
        
        # 1. Process cloud providers
        for cloud_config in profile.cloud_providers:
            if cloud_config.is_active:
                cloud_emissions = self._calculate_cloud_emissions(
                    user_id,
                    cloud_config,
                    month,
                    year
                )
                source_key = f"cloud_{cloud_config.provider}"
                emissions_by_source[source_key] = cloud_emissions
                emissions_by_scope['scope_2'] += cloud_emissions
                total_emissions += cloud_emissions
        
        # 2. Process CDN
        for cdn_config in profile.cdn_configs:
            if cdn_config.is_active and cdn_config.monthly_gb_transferred:
                cdn_emissions = self._calculate_cdn_emissions(
                    user_id,
                    cdn_config,
                    month,
                    year
                )
                emissions_by_source['cdn'] = cdn_emissions
                emissions_by_scope['scope_3'] += cdn_emissions
                total_emissions += cdn_emissions
        
        # 3. Process workforce
        if profile.workforce_config:
            workforce_emissions = self._calculate_workforce_emissions(
                user_id,
                profile.workforce_config,
                month,
                year
            )
            emissions_by_source['workforce'] = workforce_emissions
            # Split between scope 2 (office) and scope 3 (remote)
            # For simplicity, putting all in scope_3
            emissions_by_scope['scope_3'] += workforce_emissions
            total_emissions += workforce_emissions
        
        # 4. Process on-prem servers
        for onprem_config in profile.onprem_configs:
            if onprem_config.is_active:
                onprem_emissions = self._calculate_onprem_emissions(
                    user_id,
                    onprem_config,
                    month,
                    year
                )
                emissions_by_source['onprem_server'] = onprem_emissions
                emissions_by_scope['scope_1'] += onprem_emissions
                total_emissions += onprem_emissions
        
        # 5. Website SDK data (already tracked)
        website_emissions = self._get_existing_website_emissions(user_id, month, year)
        if website_emissions > 0:
            emissions_by_source['website_sdk'] = website_emissions
            emissions_by_scope['scope_3'] += website_emissions
            total_emissions += website_emissions
        
        # Store aggregated report
        self._store_monthly_report(
            user_id,
            month,
            year,
            total_emissions,
            emissions_by_scope,
            emissions_by_source
        )
        
        return {
            'total_kg': float(total_emissions),
            'by_scope': {k: float(v) for k, v in emissions_by_scope.items()},
            'by_source': {k: float(v) for k, v in emissions_by_source.items()}
        }
    
    def _calculate_cloud_emissions(
        self,
        user_id: str,
        cloud_config,
        month: int,
        year: int
    ) -> Decimal:
        if cloud_config.has_csv_data:
            emissions = self.emission_data.get_by_source_type(
                user_id,
                f"cloud_{cloud_config.provider}",
                month,
                year
            )
            if emissions:
                return sum(Decimal(str(e['kg_co2_emitted'])) for e in emissions)
        
        # Fall back to cost-based estimation if available
        if cloud_config.monthly_cost_usd:
            processor = self.dispatcher.get_processor('cloud_emissions')
            if processor:
                payload = {
                    'provider': cloud_config.provider,
                    'calculation_method': 'cost',
                    'monthly_cost_usd': float(cloud_config.monthly_cost_usd),
                    'region': cloud_config.regions[0] if cloud_config.regions else 'default'
                }
                result = processor.process(payload)
                
                # Store this emission
                reference_id = f"cloud_{cloud_config.provider}_{year}{month:02d}"
                self.emission_data.record_emission(
                    user_id=user_id,
                    source_type=f"cloud_{cloud_config.provider}",
                    scope='scope_2',
                    kg_co2=result.kg_co2_emitted,
                    emission_date=date(year, month, 1),
                    reference_id=reference_id,
                    metadata=result.metadata,
                    accuracy_level='medium'
                )
                
                return result.kg_co2_emitted
        
        return Decimal('0')
    
    def _calculate_cdn_emissions(
        self,
        user_id: str,
        cdn_config,
        month: int,
        year: int
    ) -> Decimal:
        processor = self.dispatcher.get_processor('cdn_data_transfer')
        if not processor:
            return Decimal('0')
        
        payload = {
            'provider': cdn_config.provider,
            'monthly_gb_transferred': float(cdn_config.monthly_gb_transferred),
            'regions': cdn_config.regions or ['WORLD']
        }
        
        result = processor.process(payload)
        
        # Store emission
        reference_id = f"cdn_{cdn_config.provider}_{year}{month:02d}"
        self.emission_data.record_emission(
            user_id=user_id,
            source_type='cdn',
            scope='scope_3',
            kg_co2=result.kg_co2_emitted,
            emission_date=date(year, month, 1),
            reference_id=reference_id,
            metadata=result.metadata,
            accuracy_level='medium'
        )
        
        return result.kg_co2_emitted
    
    def _calculate_workforce_emissions(
        self,
        user_id: str,
        workforce_config,
        month: int,
        year: int
    ) -> Decimal:

        processor = self.dispatcher.get_processor('workforce_emissions')
        if not processor:
            return Decimal('0')
        
        payload = {
            'total_employees': workforce_config.total_employees,
            'remote_percentage': float(workforce_config.remote_employee_percentage),
            'office_locations': [
                {
                    'city': loc.city,
                    'country': loc.country,
                    'country_code': loc.country_code,
                    'square_meters': float(loc.square_meters) if loc.square_meters else 0,
                    'employee_count': loc.employee_count
                }
                for loc in workforce_config.office_locations
            ],
            'calculation_period': 'monthly'
        }
        
        result = processor.process(payload)
        
        reference_id = f"workforce_{year}{month:02d}"
        self.emission_data.record_emission(
            user_id=user_id,
            source_type='workforce_remote',
            scope='scope_3',
            kg_co2=result.kg_co2_emitted,
            emission_date=date(year, month, 1),
            reference_id=reference_id,
            metadata=result.metadata,
            accuracy_level='estimated'
        )
        
        return result.kg_co2_emitted
    
    def _calculate_onprem_emissions(
        self,
        user_id: str,
        onprem_config,
        month: int,
        year: int
    ) -> Decimal:
        """Calculate on-premise server emissions for the month"""
        
        processor = self.dispatcher.get_processor('onprem_server')
        if not processor:
            return Decimal('0')
        
        payload = {
            'servers': [
                {
                    'name': spec.name,
                    'cpu_cores': spec.cpu_cores,
                    'ram_gb': spec.ram_gb,
                    'storage_tb': float(spec.storage_tb),
                    'avg_cpu_utilization': float(spec.avg_cpu_utilization),
                    'hours_per_day': float(spec.hours_per_day),
                    'days_per_month': spec.days_per_month
                }
                for spec in onprem_config.server_specs
            ],
            'location_country_code': onprem_config.location_country_code,
            'pue': float(onprem_config.power_usage_effectiveness),
            'calculation_period': 'monthly'
        }
        
        result = processor.process(payload)
        
        # Store emission
        reference_id = f"onprem_{year}{month:02d}"
        self.emission_data.record_emission(
            user_id=user_id,
            source_type='onprem_server',
            scope='scope_1',
            kg_co2=result.kg_co2_emitted,
            emission_date=date(year, month, 1),
            reference_id=reference_id,
            metadata=result.metadata,
            accuracy_level='estimated'
        )
        
        return result.kg_co2_emitted
    
    def _get_existing_website_emissions(
        self,
        user_id: str,
        month: int,
        year: int
    ) -> Decimal:
        emissions = self.emission_data.get_by_source_type(
            user_id,
            'website_sdk',
            month,
            year
        )
        
        if not emissions:
            return Decimal('0')
        
        return sum(Decimal(str(e['kg_co2_emitted'])) for e in emissions)
    
    def _store_monthly_report(
        self,
        user_id: str,
        month: int,
        year: int,
        total: Decimal,
        by_scope: Dict[str, Decimal],
        by_source: Dict[str, Decimal]
    ):
        from apps.event.models import MonthlyEmissionReport
        
        source_data = {
            'cloud_aws_kg': float(by_source.get('cloud_aws', 0)),
            'cloud_gcp_kg': float(by_source.get('cloud_gcp', 0)),
            'cloud_azure_kg': float(by_source.get('cloud_azure', 0)),
            'cdn_kg': float(by_source.get('cdn', 0)),
            'website_sdk_kg': float(by_source.get('website_sdk', 0)),
            'workforce_kg': float(by_source.get('workforce', 0)),
            'onprem_kg': float(by_source.get('onprem_server', 0)),
        }
        
        MonthlyEmissionReport.objects.update_or_create(
            user_id=user_id,
            year=year,
            month=month,
            defaults={
                'total_emissions_kg': total,
                'scope_1_kg': by_scope['scope_1'],
                'scope_2_kg': by_scope['scope_2'],
                'scope_3_kg': by_scope['scope_3'],
                **source_data,
                'source_breakdown': {k: float(v) for k, v in by_source.items()},
                'metadata': {
                    'calculated_at': datetime.now().isoformat()
                }
            }
        )
        
        logger.info(f"Stored monthly report for {user_id}: {year}-{month:02d}, {float(total)}kg CO2")