import logging
from rest_framework.views import APIView
from pydantic import ValidationError

from apps.auth.permissions import IsAuthenticated
from apps.common.response import response_factory
from .models import Campaign
from .schemas import (
    CreateCampaignRequest,
    UpdateCampaignRequest,
    CampaignResponse
)
from .services import CampaignService

logger = logging.getLogger(__name__)


class CampaignView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            include_archived = request.query_params.get('include_archived', 'false').lower() == 'true'
            
            campaigns = CampaignService.get_user_campaigns(user, include_archived)
            
            campaigns_data = [
                CampaignResponse(
                    id=str(campaign.external_id),
                    name=campaign.name,
                    google_ads_campaign_id=campaign.google_ads_campaign_id,
                    google_ads_customer_id=campaign.google_ads_customer_id,
                    total_impressions=campaign.total_impressions,
                    total_clicks=campaign.total_clicks,
                    total_cost_micros=campaign.total_cost_micros,
                    total_emissions_kg=float(campaign.total_emissions_kg),
                    last_synced_at=campaign.last_synced_at.isoformat() if campaign.last_synced_at else None,
                    is_archived=campaign.is_archived,
                    created_at=campaign.created_at.isoformat(),
                    updated_at=campaign.updated_at.isoformat(),
                    utm_params=[
                        {'key': param.key, 'value': param.value}
                        for param in campaign.utm_params.all()
                    ]
                ).dict() for campaign in campaigns
            ]
            
            return response_factory(
                data={'campaigns': campaigns_data, 'total_count': len(campaigns_data)},
                message="Campaigns retrieved successfully"
            )
        except Exception as e:
            logger.error(f"Error fetching campaigns: {e}", exc_info=True)
            return response_factory(
                message="Failed to fetch campaigns",
                errors={'detail': str(e)},
                status=500
            )
    
    def post(self, request):
        try:
            request_data = CreateCampaignRequest(**request.data)
            user = request.user
            
            campaign = CampaignService.create_campaign(
                user=user,
                name=request_data.name,
                google_ads_campaign_id=request_data.google_ads_campaign_id,
                google_ads_customer_id=request_data.google_ads_customer_id,
                utm_params=[param.dict() for param in request_data.utm_params] if request_data.utm_params else None
            )
            
            response_data = CampaignResponse(
                id=str(campaign.external_id),
                name=campaign.name,
                google_ads_campaign_id=campaign.google_ads_campaign_id,
                google_ads_customer_id=campaign.google_ads_customer_id,
                total_impressions=campaign.total_impressions,
                total_clicks=campaign.total_clicks,
                total_cost_micros=campaign.total_cost_micros,
                total_emissions_kg=float(campaign.total_emissions_kg),
                last_synced_at=campaign.last_synced_at.isoformat() if campaign.last_synced_at else None,
                is_archived=campaign.is_archived,
                created_at=campaign.created_at.isoformat(),
                updated_at=campaign.updated_at.isoformat(),
                utm_params=[
                    {'key': param.key, 'value': param.value}
                    for param in campaign.utm_params.all()
                ]
            ).dict()
            
            return response_factory(
                data={'campaign': response_data},
                message="Campaign created successfully"
            )
        except ValidationError as e:
            return response_factory(
                message="Validation failed",
                errors=e.errors(),
                status=400
            )
        except ValueError as e:
            return response_factory(
                message=str(e),
                status=400
            )
        except Exception as e:
            logger.error(f"Error creating campaign: {e}", exc_info=True)
            return response_factory(
                message="Failed to create campaign",
                errors={'detail': str(e)},
                status=500
            )

class CampaignDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, campaign_id):
        try:
            user = request.user
            campaign = CampaignService.get_campaign_by_id(campaign_id, user)
            
            if not campaign:
                return response_factory(
                    message="Campaign not found",
                    status=404
                )
            
            response_data = CampaignResponse(
                id=str(campaign.external_id),
                name=campaign.name,
                google_ads_campaign_id=campaign.google_ads_campaign_id,
                google_ads_customer_id=campaign.google_ads_customer_id,
                total_impressions=campaign.total_impressions,
                total_clicks=campaign.total_clicks,
                total_cost_micros=campaign.total_cost_micros,
                total_emissions_kg=float(campaign.total_emissions_kg),
                last_synced_at=campaign.last_synced_at.isoformat() if campaign.last_synced_at else None,
                is_archived=campaign.is_archived,
                created_at=campaign.created_at.isoformat(),
                updated_at=campaign.updated_at.isoformat(),
                utm_params=[
                    {'key': param.key, 'value': param.value}
                    for param in campaign.utm_params.all()
                ]
            ).dict()
            
            return response_factory(
                data={'campaign': response_data},
                message="Campaign retrieved successfully"
            )
        except Exception as e:
            logger.error(f"Error fetching campaign: {e}", exc_info=True)
            return response_factory(
                message="Failed to fetch campaign",
                errors={'detail': str(e)},
                status=500
            )
    
    def patch(self, request, campaign_id):
        try:
            user = request.user
            campaign = CampaignService.get_campaign_by_id(campaign_id, user)
            
            if not campaign:
                return response_factory(
                    message="Campaign not found",
                    status=404
                )
            
            request_data = UpdateCampaignRequest(**request.data)
            
            campaign = CampaignService.update_campaign(
                campaign=campaign,
                name=request_data.name,
                google_ads_campaign_id=request_data.google_ads_campaign_id,
                google_ads_customer_id=request_data.google_ads_customer_id,
                utm_params=[param.dict() for param in request_data.utm_params] if request_data.utm_params else None,
                is_archived=request_data.is_archived
            )
            
            response_data = CampaignResponse(
                id=str(campaign.external_id),
                name=campaign.name,
                google_ads_campaign_id=campaign.google_ads_campaign_id,
                google_ads_customer_id=campaign.google_ads_customer_id,
                total_impressions=campaign.total_impressions,
                total_clicks=campaign.total_clicks,
                total_cost_micros=campaign.total_cost_micros,
                total_emissions_kg=float(campaign.total_emissions_kg),
                last_synced_at=campaign.last_synced_at.isoformat() if campaign.last_synced_at else None,
                is_archived=campaign.is_archived,
                created_at=campaign.created_at.isoformat(),
                updated_at=campaign.updated_at.isoformat(),
                utm_params=[
                    {'key': param.key, 'value': param.value}
                    for param in campaign.utm_params.all()
                ]
            ).dict()
            
            return response_factory(
                data={'campaign': response_data},
                message="Campaign updated successfully"
            )
        except ValidationError as e:
            return response_factory(
                message="Validation failed",
                errors=e.errors(),
                status=400
            )
        except Exception as e:
            logger.error(f"Error updating campaign: {e}", exc_info=True)
            return response_factory(
                message="Failed to update campaign",
                errors={'detail': str(e)},
                status=500
            )
    
    def delete(self, request, campaign_id):
        try:
            user = request.user
            campaign = CampaignService.get_campaign_by_id(campaign_id, user)
            
            if not campaign:
                return response_factory(
                    message="Campaign not found",
                    status=404
                )
            
            hard_delete = request.query_params.get('hard_delete', 'false').lower() == 'true'
            
            if hard_delete:
                CampaignService.hard_delete_campaign(campaign)
                message = "Campaign permanently deleted successfully"
            else:
                CampaignService.delete_campaign(campaign)
                message = "Campaign archived successfully"
            
            return response_factory(
                message=message
            )
        except Exception as e:
            logger.error(f"Error deleting campaign: {e}", exc_info=True)
            return response_factory(
                message="Failed to delete campaign",
                errors={'detail': str(e)},
                status=500
            )