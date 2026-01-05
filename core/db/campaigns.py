from typing import Optional, List, Tuple
from datetime import datetime, date
from decimal import Decimal
from core.models.campaign import Campaign, CampaignEmission, UTMParameter
import logging

logger = logging.getLogger(__name__)


class CampaignData:
    def get_by_id(self, campaign_id: int) -> Optional[Campaign]:
        from apps.campaign.models import Campaign as DjangoCampaign
        
        try:
            django_campaign = DjangoCampaign.objects.prefetch_related('utm_params').get(id=campaign_id)
            return self._to_domain(django_campaign)
        except DjangoCampaign.DoesNotExist:
            return None
    
    def get_by_external_id(self, external_id: str) -> Optional[Campaign]:
        from apps.campaign.models import Campaign as DjangoCampaign
        
        try:
            django_campaign = DjangoCampaign.objects.prefetch_related('utm_params').get(external_id=external_id)
            return self._to_domain(django_campaign)
        except DjangoCampaign.DoesNotExist:
            return None
    
    def get_user_campaigns(self, user_id: str, include_archived: bool = False) -> List[Campaign]:
        from apps.campaign.models import Campaign as DjangoCampaign
        
        queryset = DjangoCampaign.objects.filter(user_id=user_id).prefetch_related('utm_params')
        
        if not include_archived:
            queryset = queryset.filter(is_archived=False)
        
        return [self._to_domain(c) for c in queryset.order_by('-created_at')]
    
    def create(self, user_id: str, name: str, 
               google_ads_campaign_id: Optional[str] = None,
               google_ads_customer_id: Optional[str] = None,
               utm_params: List[UTMParameter] = None) -> Campaign:
        from apps.campaign.models import Campaign as DjangoCampaign
        from apps.campaign.models import UTMParameter as DjangoUTMParameter
        from apps.auth.models import User as DjangoUser
        
        user = DjangoUser.objects.get(id=user_id)
        
        django_campaign = DjangoCampaign.objects.create(
            user=user,
            name=name,
            google_ads_campaign_id=google_ads_campaign_id,
            google_ads_customer_id=google_ads_customer_id
        )
        
        if utm_params:
            utm_objects = [
                DjangoUTMParameter(
                    campaign=django_campaign,
                    user=user,
                    key=utm.key,
                    value=utm.value
                )
                for utm in utm_params
            ]
            DjangoUTMParameter.objects.bulk_create(utm_objects)
        
        django_campaign.refresh_from_db()
        return self._to_domain(django_campaign)
    
    def update(self, campaign_id: int, **kwargs) -> Campaign:
        from apps.campaign.models import Campaign as DjangoCampaign
        
        django_campaign = DjangoCampaign.objects.get(id=campaign_id)
        
        for key, value in kwargs.items():
            if hasattr(django_campaign, key):
                setattr(django_campaign, key, value)
        
        django_campaign.save()
        django_campaign.refresh_from_db()
        
        return self._to_domain(django_campaign)
    
    def update_utm_params(self, campaign_id: int, utm_params: List[UTMParameter]) -> Campaign:
        from apps.campaign.models import Campaign as DjangoCampaign
        from apps.campaign.models import UTMParameter as DjangoUTMParameter
        
        django_campaign = DjangoCampaign.objects.get(id=campaign_id)
        
        DjangoUTMParameter.objects.filter(campaign=django_campaign).delete()
        
        utm_objects = [
            DjangoUTMParameter(
                campaign=django_campaign,
                user=django_campaign.user,
                key=utm.key,
                value=utm.value
            )
            for utm in utm_params
        ]
        DjangoUTMParameter.objects.bulk_create(utm_objects)
        
        django_campaign.refresh_from_db()
        return self._to_domain(django_campaign)
    
    def delete(self, campaign_id: int, soft_delete: bool = True) -> bool:
        from apps.campaign.models import Campaign as DjangoCampaign
        
        try:
            django_campaign = DjangoCampaign.objects.get(id=campaign_id)
            
            if soft_delete:
                django_campaign.is_archived = True
                django_campaign.save()
            else:
                django_campaign.delete()
            
            return True
        except DjangoCampaign.DoesNotExist:
            return False
    
    def find_matching_campaign(self, user_id: str, utm_params: dict) -> Optional[Campaign]:
        from apps.campaign.models import Campaign as DjangoCampaign
        
        campaigns = DjangoCampaign.objects.filter(
            user_id=user_id,
            is_archived=False
        ).prefetch_related('utm_params')
        
        for django_campaign in campaigns:
            campaign_utms = {
                utm.key: utm.value 
                for utm in django_campaign.utm_params.all()
            }
            
            if all(utm_params.get(key) == value for key, value in campaign_utms.items()):
                return self._to_domain(django_campaign)
        
        return None
    
    def _to_domain(self, django_campaign) -> Campaign:
        utm_params = [
            UTMParameter(key=utm.key, value=utm.value)
            for utm in django_campaign.utm_params.all()
        ]
        
        return Campaign(
            id=django_campaign.id,
            external_id=django_campaign.external_id,
            user_id=str(django_campaign.user_id),
            name=django_campaign.name,
            google_ads_campaign_id=django_campaign.google_ads_campaign_id,
            google_ads_customer_id=django_campaign.google_ads_customer_id,
            total_impressions=django_campaign.total_impressions,
            total_clicks=django_campaign.total_clicks,
            total_cost_micros=django_campaign.total_cost_micros,
            total_emissions_kg=django_campaign.total_emissions_kg,
            utm_params=utm_params,
            last_synced_at=django_campaign.last_synced_at,
            is_archived=django_campaign.is_archived,
            created_at=django_campaign.created_at,
            updated_at=django_campaign.updated_at,
        )


class CampaignEmissionData:
    def get_campaign_emissions(self, campaign_id: int, 
                               start_date: Optional[date] = None,
                               end_date: Optional[date] = None) -> List[CampaignEmission]:
        from apps.campaign.models import CampaignEmission as DjangoEmission
        
        queryset = DjangoEmission.objects.filter(campaign_id=campaign_id)
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return [self._to_domain(e) for e in queryset.order_by('-date', '-hour')]
    
    def create_or_update(self, campaign_id: int, emission_date: date,
                        country: str, device_type: str,
                        hour: Optional[int] = None, region: str = '',
                        **metrics) -> CampaignEmission:
        from apps.campaign.models import CampaignEmission as DjangoEmission
        
        emission, created = DjangoEmission.objects.update_or_create(
            campaign_id=campaign_id,
            date=emission_date,
            country=country,
            device_type=device_type,
            hour=hour,
            region=region,
            defaults=metrics
        )
        
        return self._to_domain(emission)
    
    def bulk_create_or_update(self, emissions_data: List[dict]) -> int:
        """Bulk create or update emissions"""
        from apps.campaign.models import CampaignEmission as DjangoEmission
        
        count = 0
        for data in emissions_data:
            emission, created = DjangoEmission.objects.update_or_create(
                campaign_id=data['campaign_id'],
                date=data['date'],
                country=data.get('country', 'United States'),
                device_type=data.get('device_type', 'desktop'),
                hour=data.get('hour'),
                region=data.get('region', ''),
                defaults={
                    'impressions': data.get('impressions', 0),
                    'ad_clicks': data.get('ad_clicks', 0),
                    'cost_micros': data.get('cost_micros', 0),
                    'impression_emissions_g': data.get('impression_emissions_g', Decimal('0')),
                    'page_view_emissions_g': data.get('page_view_emissions_g', Decimal('0')),
                    'click_emissions_g': data.get('click_emissions_g', Decimal('0')),
                    'conversion_emissions_g': data.get('conversion_emissions_g', Decimal('0')),
                    'total_emissions_g': data.get('total_emissions_g', Decimal('0')),
                }
            )
            count += 1
        
        return count
    
    def _to_domain(self, django_emission) -> CampaignEmission:
        return CampaignEmission(
            id=django_emission.id,
            external_id=django_emission.external_id,
            campaign_id=django_emission.campaign_id,
            date=django_emission.date,
            hour=django_emission.hour,
            country=django_emission.country,
            region=django_emission.region,
            city=django_emission.city,
            device_type=django_emission.device_type,
            page_views=django_emission.page_views,
            clicks=django_emission.clicks,
            conversions=django_emission.conversions,
            sessions=django_emission.sessions,
            impressions=django_emission.impressions,
            ad_clicks=django_emission.ad_clicks,
            cost_micros=django_emission.cost_micros,
            impression_emissions_g=django_emission.impression_emissions_g,
            page_view_emissions_g=django_emission.page_view_emissions_g,
            click_emissions_g=django_emission.click_emissions_g,
            conversion_emissions_g=django_emission.conversion_emissions_g,
            total_emissions_g=django_emission.total_emissions_g,
            created_at=django_emission.created_at,
            updated_at=django_emission.updated_at,
        )