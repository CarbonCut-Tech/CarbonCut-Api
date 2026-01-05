from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from core.models.campaign import (
    Campaign, 
    CampaignEmission, 
    CreateCampaignRequest,
    UpdateCampaignRequest,
    GoogleAdsImpressionData,
    UTMParameter
)
from core.db.campaigns import CampaignData, CampaignEmissionData
import logging

logger = logging.getLogger(__name__)


class CampaignService:
    def __init__(self):
        self.campaign_repo = CampaignData()
        self.emission_repo = CampaignEmissionData()
    
    def get_campaign(self, campaign_id: int) -> Optional[Campaign]:
        return self.campaign_repo.get_by_id(campaign_id)
    
    def get_campaign_by_external_id(self, external_id: str) -> Optional[Campaign]:
        return self.campaign_repo.get_by_external_id(external_id)
    
    def list_user_campaigns(self, user_id: str, include_archived: bool = False) -> List[Campaign]:
        return self.campaign_repo.get_user_campaigns(user_id, include_archived)
    
    def create_campaign(self, user_id: str, request: CreateCampaignRequest) -> Campaign:
        logger.info(f"Creating campaign for user {user_id}: {request.name}")
        
        campaign = self.campaign_repo.create(
            user_id=user_id,
            name=request.name,
            google_ads_campaign_id=request.google_ads_campaign_id,
            google_ads_customer_id=request.google_ads_customer_id,
            utm_params=request.utm_params
        )
        
        logger.info(f"Campaign created: {campaign.external_id}")
        return campaign
    
    def update_campaign(self, campaign_id: int, request: UpdateCampaignRequest) -> Campaign:
        update_data = {}
        
        if request.name is not None:
            update_data['name'] = request.name
        
        campaign = self.campaign_repo.update(campaign_id, **update_data)
        
        if request.utm_params is not None:
            campaign = self.campaign_repo.update_utm_params(campaign_id, request.utm_params)
        
        return campaign
    
    def delete_campaign(self, campaign_id: int, soft_delete: bool = True) -> bool:
        return self.campaign_repo.delete(campaign_id, soft_delete)
    
    def match_session_to_campaign(self, user_id: str, utm_params: dict) -> Optional[Campaign]:
        if not utm_params:
            return None
        
        return self.campaign_repo.find_matching_campaign(user_id, utm_params)
    
    def update_campaign_metrics(self, campaign_id: int) -> Campaign:
        from apps.campaign.models import CampaignEmission as DjangoEmission
        from django.db.models import Sum
        
        emissions = DjangoEmission.objects.filter(campaign_id=campaign_id)
        
        aggregates = emissions.aggregate(
            total_impressions=Sum('impressions'),
            total_clicks=Sum('ad_clicks'),
            total_cost=Sum('cost_micros'),
            total_emissions=Sum('total_emissions_g')
        )
        
        total_emissions_kg = Decimal(aggregates['total_emissions'] or 0) / 1000  # Convert g to kg
        
        campaign = self.campaign_repo.update(
            campaign_id,
            total_impressions=aggregates['total_impressions'] or 0,
            total_clicks=aggregates['total_clicks'] or 0,
            total_cost_micros=aggregates['total_cost'] or 0,
            total_emissions_kg=total_emissions_kg
        )
        
        logger.info(f"Updated campaign metrics for {campaign_id}")
        return campaign
    
    def sync_google_ads_impressions(self, campaign_id: int, 
                                    impressions_data: List[GoogleAdsImpressionData]) -> Tuple[int, str]:
        logger.info(f"Syncing {len(impressions_data)} impression records for campaign {campaign_id}")
        
        emissions_to_create = []
        
        for record in impressions_data:
            impression_emissions = Decimal(record.impressions) * Decimal('0.0002')
            
            emissions_to_create.append({
                'campaign_id': campaign_id,
                'date': record.date,
                'country': record.country,
                'device_type': record.device_type,
                'hour': None,  
                'region': '',
                'impressions': record.impressions,
                'ad_clicks': record.clicks,
                'cost_micros': record.cost_micros,
                'impression_emissions_g': impression_emissions,
                'total_emissions_g': impression_emissions,  
            })
        
        count = self.emission_repo.bulk_create_or_update(emissions_to_create)
        
        self.campaign_repo.update(campaign_id, last_synced_at=datetime.now())
        self.update_campaign_metrics(campaign_id)
        
        logger.info(f"Synced {count} emission records for campaign {campaign_id}")
        return count, f"Successfully synced {count} records"


class CampaignAnalyticsService:
    def __init__(self):
        self.emission_repo = CampaignEmissionData()
    
    def get_campaign_analytics(self, campaign_id: int, 
                              start_date: date, end_date: date,
                              group_by: str = 'day') -> Dict[str, Any]:
        from apps.campaign.models import CampaignEmission as DjangoEmission
        from django.db.models import Sum
        
        emissions = DjangoEmission.objects.filter(
            campaign_id=campaign_id,
            date__gte=start_date,
            date__lte=end_date
        )
        summary = emissions.aggregate(
            total_impressions=Sum('impressions'),
            total_ad_clicks=Sum('ad_clicks'),
            total_page_views=Sum('page_views'),
            total_clicks=Sum('clicks'),
            total_conversions=Sum('conversions'),
            total_sessions=Sum('sessions'),
            total_cost=Sum('cost_micros'),
            total_emissions_g=Sum('total_emissions_g'),
        )
        
        for key in summary:
            if summary[key] is None:
                summary[key] = 0
        
        timeline = []
        if group_by == 'day':
            timeline = list(emissions.values('date').annotate(
                impressions=Sum('impressions'),
                emissions_g=Sum('total_emissions_g'),
                page_views=Sum('page_views'),
                conversions=Sum('conversions'),
            ).order_by('date'))
        elif group_by == 'country':
            timeline = list(emissions.values('country').annotate(
                impressions=Sum('impressions'),
                emissions_g=Sum('total_emissions_g'),
                page_views=Sum('page_views'),
                conversions=Sum('conversions'),
            ).order_by('-impressions'))
        elif group_by == 'device':
            timeline = list(emissions.values('device_type').annotate(
                impressions=Sum('impressions'),
                emissions_g=Sum('total_emissions_g'),
                page_views=Sum('page_views'),
                conversions=Sum('conversions'),
            ).order_by('-impressions'))
        
        return {
            'summary': summary,
            'timeline': timeline,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },
            'group_by': group_by
        }