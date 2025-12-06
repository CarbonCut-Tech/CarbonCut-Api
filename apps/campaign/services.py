import logging
from typing import List, Optional, Dict
from django.db import transaction

from .models import Campaign, UTMParameter
from apps.auth.models import User

logger = logging.getLogger(__name__)

class CampaignService:
    @staticmethod
    def create_campaign(
        user: User,
        name: str,
        google_ads_campaign_id: Optional[str] = None,
        google_ads_customer_id: Optional[str] = None,
        utm_params: Optional[List[Dict[str, str]]] = None
    ) -> Campaign:
        with transaction.atomic():
            if google_ads_campaign_id and google_ads_customer_id:
                existing = Campaign.objects.filter(
                    user=user,
                    google_ads_campaign_id=google_ads_campaign_id,
                    google_ads_customer_id=google_ads_customer_id,
                    is_archived=False
                ).first()
                
                if existing:
                    raise ValueError("A campaign with this Google Ads Campaign ID already exists")
            
            campaign = Campaign.objects.create(
                user=user,
                name=name,
                google_ads_campaign_id=google_ads_campaign_id,
                google_ads_customer_id=google_ads_customer_id
            )
            
            if utm_params:
                utm_objects = [
                    UTMParameter(
                        campaign=campaign,
                        key=param['key'],
                        value=param['value']
                    )
                    for param in utm_params
                ]
                UTMParameter.objects.bulk_create(utm_objects)
            
            logger.info(f"Campaign created: {name} for user {user.id}")
            return campaign

    @staticmethod
    def get_user_campaigns(user: User, include_archived: bool = False) -> List[Campaign]:
        queryset = Campaign.objects.filter(user=user)
        
        if not include_archived:
            queryset = queryset.filter(is_archived=False)
        
        return queryset.prefetch_related('utm_params').order_by('-created_at')

    @staticmethod
    def get_campaign_by_id(campaign_id: str, user: User) -> Optional[Campaign]:
        try:
            return Campaign.objects.prefetch_related('utm_params').get(
                external_id=campaign_id,
                user=user
            )
        except Campaign.DoesNotExist:
            try:
                return Campaign.objects.prefetch_related('utm_params').get(
                    id=int(campaign_id),
                    user=user
                )
            except (Campaign.DoesNotExist, ValueError):
                return None

    @staticmethod
    def update_campaign(
        campaign: Campaign,
        name: Optional[str] = None,
        google_ads_campaign_id: Optional[str] = None,
        google_ads_customer_id: Optional[str] = None,
        utm_params: Optional[List[Dict[str, str]]] = None,
        is_archived: Optional[bool] = None
    ) -> Campaign:
        with transaction.atomic():
            update_fields = ['updated_at']
            
            if name is not None:
                campaign.name = name
                update_fields.append('name')
            
            if google_ads_campaign_id is not None:
                campaign.google_ads_campaign_id = google_ads_campaign_id
                update_fields.append('google_ads_campaign_id')
            
            if google_ads_customer_id is not None:
                campaign.google_ads_customer_id = google_ads_customer_id
                update_fields.append('google_ads_customer_id')
            
            if is_archived is not None:
                campaign.is_archived = is_archived
                update_fields.append('is_archived')
            
            campaign.save(update_fields=update_fields)
            
            if utm_params is not None:
                UTMParameter.objects.filter(campaign=campaign).delete()
                
                if utm_params:
                    utm_objects = [
                        UTMParameter(
                            campaign=campaign,
                            key=param['key'],
                            value=param['value']
                        )
                        for param in utm_params
                    ]
                    UTMParameter.objects.bulk_create(utm_objects)
            
            logger.info(f"Campaign updated: {campaign.name}")
            return campaign

    @staticmethod
    def delete_campaign(campaign: Campaign) -> None:
        campaign.is_archived = True
        campaign.save(update_fields=['is_archived', 'updated_at'])
        logger.info(f"Campaign archived: {campaign.name}")

    @staticmethod
    def hard_delete_campaign(campaign: Campaign) -> None:
        campaign_name = campaign.name
        campaign.delete()
        logger.info(f"Campaign permanently deleted: {campaign_name}")