from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from core.models.emission_config import (
    CloudProviderConfig,
    CDNConfig,
    WorkforceConfig,
    OnPremConfig,
    UserEmissionProfile,
    ServerSpec,
    OfficeLocation
)
import logging
logger = logging.getLogger(__name__)
class EmissionSourceData:
    def record_emission(
        self,
        user_id: str,
        source_type: str,
        scope: str,
        kg_co2: Decimal,
        emission_date: date,
        reference_id: str,
        metadata: Dict[str, Any],
        accuracy_level: str = 'estimated'
    ) -> str:
        from apps.event.models import EmissionSource
        
        emission = EmissionSource.objects.create(
            user_id=user_id,
            source_type=source_type,
            scope=scope,
            kg_co2_emitted=kg_co2,
            emission_date=emission_date,
            reference_id=reference_id,
            metadata=metadata,
            accuracy_level=accuracy_level
        )
        
        logger.info(f"Recorded {source_type} emission: {kg_co2}kg CO2e for user {user_id}")
        return str(emission.id)
    
    def get_by_date_range(
        self,
        user_id: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        from apps.event.models import EmissionSource
        
        emissions = EmissionSource.objects.filter(
            user_id=user_id,
            emission_date__gte=start_date,
            emission_date__lte=end_date
        ).values()
        
        return list(emissions)
    
    def get_by_source_type(
        self,
        user_id: str,
        source_type: str,
        month: int,
        year: int
    ) -> List[Dict[str, Any]]:
        from apps.event.models import EmissionSource
        
        emissions = EmissionSource.objects.filter(
            user_id=user_id,
            source_type=source_type,
            emission_date__year=year,
            emission_date__month=month
        ).values()
        
        return list(emissions)
    
    def get_monthly_summary(
        self,
        user_id: str,
        month: int,
        year: int
    ) -> Dict[str, Any]:
        from apps.event.models import EmissionSource
        from django.db.models import Sum
        source_totals = EmissionSource.objects.filter(
            user_id=user_id,
            emission_date__year=year,
            emission_date__month=month
        ).values('source_type', 'scope').annotate(
            total_kg=Sum('kg_co2_emitted')
        )

        scope_totals = EmissionSource.objects.filter(
            user_id=user_id,
            emission_date__year=year,
            emission_date__month=month
        ).values('scope').annotate(
            total_kg=Sum('kg_co2_emitted')
        )
        
        total = EmissionSource.objects.filter(
            user_id=user_id,
            emission_date__year=year,
            emission_date__month=month
        ).aggregate(total=Sum('kg_co2_emitted'))
        
        return {
            'user_id': user_id,
            'year': year,
            'month': month,
            'total_kg': total['total'] or Decimal('0'),
            'by_source': {item['source_type']: item['total_kg'] for item in source_totals},
            'by_scope': {item['scope']: item['total_kg'] for item in scope_totals}
        }


class CloudProviderData:
    def create(self, config: CloudProviderConfig) -> CloudProviderConfig:
        from apps.event.models import CloudProviderConnection
        connection, created = CloudProviderConnection.objects.update_or_create(
            user_id=config.user_id,
            provider=config.provider,
            defaults={
                'connection_type': config.connection_type,
                'regions': config.regions,
                'monthly_cost_usd': config.monthly_cost_usd,
                'has_csv_data': config.has_csv_data,
                'last_csv_upload_date': config.last_csv_upload_date,
                'csv_file_path': config.csv_file_path,
                'is_active': config.is_active,
                'metadata': config.metadata,
            }
        )
        
        return self._to_domain(connection)
    
    def get_by_user(self, user_id: str) -> List[CloudProviderConfig]:
        from apps.event.models import CloudProviderConnection
        
        connections = CloudProviderConnection.objects.filter(
            user_id=user_id,
            is_active=True
        )
        
        return [self._to_domain(conn) for conn in connections]
    
    def _to_domain(self, orm) -> CloudProviderConfig:
        return CloudProviderConfig(
            id=str(orm.id),
            user_id=orm.user_id,
            provider=orm.provider,
            connection_type=orm.connection_type,
            regions=orm.regions,
            monthly_cost_usd=orm.monthly_cost_usd,
            has_csv_data=orm.has_csv_data,
            last_csv_upload_date=orm.last_csv_upload_date,
            csv_file_path=orm.csv_file_path,
            is_active=orm.is_active,
            metadata=orm.metadata,
            created_at=orm.created_at,
            updated_at=orm.updated_at
        )


class UserEmissionProfileData:
    def get_profile(self, user_id: str) -> Optional[UserEmissionProfile]:
        cloud_data = CloudProviderData()
        cdn_data = CDNData()
        workforce_data = WorkforceData()
        onprem_data = OnPremData()
        
        cloud_providers = cloud_data.get_by_user(user_id)
        cdn_configs = cdn_data.get_by_user(user_id)
        workforce_config = workforce_data.get_by_user(user_id)
        onprem_configs = onprem_data.get_by_user(user_id)
        if not (cloud_providers or cdn_configs or workforce_config or onprem_configs):
            return None
        
        return UserEmissionProfile(
            user_id=user_id,
            cloud_providers=cloud_providers,
            cdn_configs=cdn_configs,
            workforce_config=workforce_config,
            onprem_configs=onprem_configs,
            onboarding_completed=bool(cloud_providers or cdn_configs)
        )


class CDNData:
    """Data access for CDN configurations"""
    
    def get_by_user(self, user_id: str) -> List[CDNConfig]:
        from apps.event.models import CDNConnection
        
        connections = CDNConnection.objects.filter(user_id=user_id, is_active=True)
        return [self._to_domain(conn) for conn in connections]
    
    def create(self, config: CDNConfig) -> CDNConfig:
        from apps.event.models import CDNConnection
        
        connection = CDNConnection.objects.create(
            user_id=config.user_id,
            provider=config.provider,
            connection_type=config.connection_type,
            monthly_gb_transferred=config.monthly_gb_transferred,
            regions=config.regions,
            metadata=config.metadata
        )
        return self._to_domain(connection)
    
    def _to_domain(self, orm) -> CDNConfig:
        return CDNConfig(
            id=str(orm.id),
            user_id=orm.user_id,
            provider=orm.provider,
            connection_type=orm.connection_type,
            monthly_gb_transferred=orm.monthly_gb_transferred,
            regions=orm.regions,
            metadata=orm.metadata,
            created_at=orm.created_at,
            updated_at=orm.updated_at
        )


class WorkforceData:
    def get_by_user(self, user_id: str) -> Optional[WorkforceConfig]:
        from apps.event.models import WorkforceConfiguration
        
        try:
            config = WorkforceConfiguration.objects.get(user_id=user_id)
            return self._to_domain(config)
        except WorkforceConfiguration.DoesNotExist:
            return None
    
    def create_or_update(self, config: WorkforceConfig) -> WorkforceConfig:
        from apps.event.models import WorkforceConfiguration
        
        workforce, created = WorkforceConfiguration.objects.update_or_create(
            user_id=config.user_id,
            defaults={
                'total_employees': config.total_employees,
                'remote_employee_percentage': config.remote_employee_percentage,
                'office_locations': [
                    {
                        'city': loc.city,
                        'country': loc.country,
                        'country_code': loc.country_code,
                        'square_meters': float(loc.square_meters) if loc.square_meters else None,
                        'employee_count': loc.employee_count
                    }
                    for loc in config.office_locations
                ],
                'travel_tracking_enabled': config.travel_tracking_enabled,
                'metadata': config.metadata
            }
        )
        return self._to_domain(workforce)
    
    def _to_domain(self, orm) -> WorkforceConfig:
        office_locations = [
            OfficeLocation(
                city=loc['city'],
                country=loc['country'],
                country_code=loc['country_code'],
                square_meters=Decimal(str(loc['square_meters'])) if loc.get('square_meters') else None,
                employee_count=loc.get('employee_count')
            )
            for loc in orm.office_locations
        ]
        
        return WorkforceConfig(
            id=str(orm.id),
            user_id=orm.user_id,
            total_employees=orm.total_employees,
            remote_employee_percentage=orm.remote_employee_percentage,
            office_locations=office_locations,
            travel_tracking_enabled=orm.travel_tracking_enabled,
            last_travel_upload_date=orm.last_travel_upload_date,
            metadata=orm.metadata,
            created_at=orm.created_at,
            updated_at=orm.updated_at
        )


class OnPremData:
    def get_by_user(self, user_id: str) -> List[OnPremConfig]:
        from apps.event.models import OnPremiseConfiguration
        
        servers = OnPremiseConfiguration.objects.filter(user_id=user_id, is_active=True)
        configs_by_location = {}
        for server in servers:
            key = f"{server.location_city}_{server.location_country_code}"
            if key not in configs_by_location:
                configs_by_location[key] = {
                    'location_city': server.location_city,
                    'location_country_code': server.location_country_code,
                    'pue': server.power_usage_effectiveness,
                    'servers': []
                }
            configs_by_location[key]['servers'].append(server)
        
        configs = []
        for key, data in configs_by_location.items():
            server_specs = [
                ServerSpec(
                    name=srv.server_name,
                    cpu_cores=srv.cpu_cores,
                    ram_gb=srv.ram_gb,
                    storage_tb=srv.storage_tb,
                    avg_cpu_utilization=srv.avg_cpu_utilization / 100,  # Convert to 0-1
                    hours_per_day=srv.hours_per_day,
                    days_per_month=srv.days_per_month
                )
                for srv in data['servers']
            ]
            
            configs.append(OnPremConfig(
                id=str(data['servers'][0].id),
                user_id=user_id,
                server_specs=server_specs,
                location_city=data['location_city'],
                location_country_code=data['location_country_code'],
                power_usage_effectiveness=data['pue']
            ))
        
        return configs
    
    def create(self, config: OnPremConfig) -> None:
        from apps.event.models import OnPremiseConfiguration
        
        for server_spec in config.server_specs:
            OnPremiseConfiguration.objects.create(
                user_id=config.user_id,
                server_name=server_spec.name,
                cpu_cores=server_spec.cpu_cores,
                ram_gb=server_spec.ram_gb,
                storage_tb=server_spec.storage_tb,
                avg_cpu_utilization=server_spec.avg_cpu_utilization * 100,  # Convert to percentage
                hours_per_day=server_spec.hours_per_day,
                days_per_month=server_spec.days_per_month,
                location_city=config.location_city,
                location_country_code=config.location_country_code,
                power_usage_effectiveness=config.power_usage_effectiveness,
                metadata=config.metadata
            )