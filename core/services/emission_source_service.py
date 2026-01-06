from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import logging
from core.models.emission_config import ( CloudProviderConfig,CDNConfig,WorkforceConfig,OnPremConfig,UserEmissionProfile,ServerSpec,OfficeLocation )
from core.db.emission_sources import ( CloudProviderData,CDNData,WorkforceData,OnPremData,UserEmissionProfileData)

logger = logging.getLogger(__name__)
class EmissionSourceService:
    def __init__(self):
        self.cloud_data = CloudProviderData()
        self.cdn_data = CDNData()
        self.workforce_data = WorkforceData()
        self.onprem_data = OnPremData()
        self.profile_data = UserEmissionProfileData()
    
    def configure_emission_sources(
        self,
        user_id: str,
        cloud_providers: List[Dict[str, Any]],
        cdn_providers: List[Dict[str, Any]],
        workforce: Optional[Dict[str, Any]],
        onprem_servers: List[Dict[str, Any]]
    ) -> UserEmissionProfile:
        logger.info(f"Configuring emission sources for user {user_id}")
        cloud_configs = []
        for provider_data in cloud_providers:
            config = CloudProviderConfig(
                id='',
                user_id=user_id,
                provider=provider_data['provider'],
                connection_type=provider_data['connection_method'],
                regions=provider_data.get('regions', []),
                monthly_cost_usd=provider_data.get('monthly_cost_usd'),
                has_csv_data=False,
                metadata={}
            )
            saved_config = self.cloud_data.create(config)
            cloud_configs.append(saved_config)

        cdn_configs = []
        for cdn_data_input in cdn_providers:
            config = CDNConfig(
                id='',
                user_id=user_id,
                provider=cdn_data_input['provider'],
                connection_type='manual',
                monthly_gb_transferred=cdn_data_input.get('monthly_gb_transferred'),
                regions=cdn_data_input.get('regions', []),
                metadata={}
            )
            saved_config = self.cdn_data.create(config)
            cdn_configs.append(saved_config)
    
        workforce_config = None
        if workforce:
            office_locations = [
                OfficeLocation(
                    city=loc['city'],
                    country=loc['country'],
                    country_code=loc['country_code'],
                    square_meters=Decimal(str(loc.get('square_meters', 0))) if loc.get('square_meters') else None,
                    employee_count=loc.get('employee_count')
                )
                for loc in workforce.get('office_locations', [])
            ]
            
            config = WorkforceConfig(
                id='',
                user_id=user_id,
                total_employees=workforce['total_employees'],
                remote_employee_percentage=workforce['remote_percentage'],
                office_locations=office_locations,
                travel_tracking_enabled=workforce.get('track_travel', False),
                metadata={}
            )
            workforce_config = self.workforce_data.create_or_update(config)
        
        onprem_configs = []
        if onprem_servers:
            servers_by_location = {}
            for server in onprem_servers:
                key = f"{server['location_city']}_{server['location_country_code']}"
                if key not in servers_by_location:
                    servers_by_location[key] = {
                        'city': server['location_city'],
                        'country_code': server['location_country_code'],
                        'pue': server.get('power_usage_effectiveness', Decimal('1.6')),
                        'servers': []
                    }
                servers_by_location[key]['servers'].append(server)
            
            for location_data in servers_by_location.values():
                server_specs = [
                    ServerSpec(
                        name=srv['name'],
                        cpu_cores=srv['cpu_cores'],
                        ram_gb=srv['ram_gb'],
                        storage_tb=Decimal(str(srv['storage_tb'])),
                        avg_cpu_utilization=Decimal(str(srv.get('avg_cpu_utilization', 50))) / 100,
                        hours_per_day=Decimal(str(srv.get('hours_per_day', 24))),
                        days_per_month=srv.get('days_per_month', 30)
                    )
                    for srv in location_data['servers']
                ]
                
                config = OnPremConfig(
                    id='',
                    user_id=user_id,
                    server_specs=server_specs,
                    location_city=location_data['city'],
                    location_country_code=location_data['country_code'],
                    power_usage_effectiveness=location_data['pue'],
                    metadata={}
                )
                self.onprem_data.create(config)
                onprem_configs.append(config)
        
        logger.info(
            f"Emission sources configured for user {user_id}: "
            f"{len(cloud_configs)} cloud, {len(cdn_configs)} CDN, "
            f"{'1' if workforce_config else '0'} workforce, {len(onprem_configs)} on-prem"
        )
        
        return UserEmissionProfile(
            user_id=user_id,
            cloud_providers=cloud_configs,
            cdn_configs=cdn_configs,
            workforce_config=workforce_config,
            onprem_configs=onprem_configs,
            onboarding_completed=True
        )
    
    def get_user_profile(self, user_id: str) -> Optional[UserEmissionProfile]:
        return self.profile_data.get_profile(user_id)
    
    def update_cloud_provider(
        self,
        user_id: str,
        provider: str,
        updates: Dict[str, Any]
    ) -> CloudProviderConfig:
        existing = self.cloud_data.get_by_user(user_id)
        provider_config = next((c for c in existing if c.provider == provider), None)
        
        if not provider_config:
            raise ValueError(f"Cloud provider {provider} not configured for user {user_id}")
        if 'regions' in updates:
            provider_config.regions = updates['regions']
        if 'monthly_cost_usd' in updates:
            provider_config.monthly_cost_usd = updates['monthly_cost_usd']
        if 'connection_type' in updates:
            provider_config.connection_type = updates['connection_type']
        
        return self.cloud_data.create(provider_config)
    
    def mark_csv_uploaded(
        self,
        user_id: str,
        provider: str,
        csv_file_path: str
    ) -> CloudProviderConfig:
        existing = self.cloud_data.get_by_user(user_id)
        provider_config = next((c for c in existing if c.provider == provider), None)
        
        if not provider_config:
            raise ValueError(f"Cloud provider {provider} not configured for user {user_id}")
        
        provider_config.has_csv_data = True
        provider_config.last_csv_upload_date = datetime.now()
        provider_config.csv_file_path = csv_file_path
        
        return self.cloud_data.create(provider_config)