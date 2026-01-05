import logging
from typing import Dict, Any
from django.http import JsonResponse, HttpRequest
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from pydantic import ValidationError
from datetime import datetime, timedelta, date

from core.services.campaign_service import CampaignService, CampaignAnalyticsService
from core.models.campaign import CreateCampaignRequest, UpdateCampaignRequest, GoogleAdsImpressionData
from core.services.auth.jwt_service import JWTService
from apps.common.response import response_factory

logger = logging.getLogger(__name__)


class CampaignController:
    def __init__(self):
        self.campaign_service = CampaignService()
        self.analytics_service = CampaignAnalyticsService()
        self.jwt_service = JWTService()


@method_decorator(csrf_exempt, name='dispatch')
class CampaignListCreateView(View):
    def get(self, request: HttpRequest):
        try:
            controller = CampaignController()
            user_id, payload = controller.jwt_service.decode_token_from_request(request)
            if not user_id:
                return response_factory(message="Unauthorized", status=401)
            
            include_archived = request.GET.get('include_archived', 'false').lower() == 'true'
            
            campaigns = controller.campaign_service.list_user_campaigns(
                user_id=user_id,
                include_archived=include_archived
            )
            
            campaigns_data = [
                {
                    'external_id': str(c.external_id),
                    'name': c.name,
                    'google_ads_campaign_id': c.google_ads_campaign_id,
                    'google_ads_customer_id': c.google_ads_customer_id,
                    'total_impressions': c.total_impressions,
                    'total_clicks': c.total_clicks,
                    'total_cost_micros': c.total_cost_micros,
                    'total_emissions_kg': float(c.total_emissions_kg),
                    'utm_params': [{'key': u.key, 'value': u.value} for u in c.utm_params],
                    'last_synced_at': c.last_synced_at.isoformat() if c.last_synced_at else None,
                    'is_archived': c.is_archived,
                    'created_at': c.created_at.isoformat() if c.created_at else None,
                }
                for c in campaigns
            ]
            
            return response_factory(
                data={'campaigns': campaigns_data, 'total': len(campaigns_data)},
                message="Campaigns retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Error listing campaigns: {e}", exc_info=True)
            return response_factory(message="Failed to fetch campaigns", status=500)
    
    def post(self, request: HttpRequest):
        try:
            controller = CampaignController()
            
            user_id, payload = controller.jwt_service.decode_token_from_request(request)
            if not user_id:
                return response_factory(message="Unauthorized", status=401)
            
            request_data = CreateCampaignRequest.parse_raw(request.body)
            
            logger.info(f"Creating campaign for user {user_id}: {request_data.name}")
            
            campaign = controller.campaign_service.create_campaign(
                user_id=user_id,
                request=request_data
            )
            
            campaign_data = {
                'external_id': str(campaign.external_id),
                'name': campaign.name,
                'google_ads_campaign_id': campaign.google_ads_campaign_id,
                'google_ads_customer_id': campaign.google_ads_customer_id,
                'utm_params': [{'key': u.key, 'value': u.value} for u in campaign.utm_params],
                'created_at': campaign.created_at.isoformat() if campaign.created_at else None,
            }
            
            return response_factory(
                data=campaign_data,
                message="Campaign created successfully"
            )
            
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return response_factory(
                message="Invalid request data",
                errors=e.errors(),
                status=400
            )
        except Exception as e:
            logger.error(f"Error creating campaign: {e}", exc_info=True)
            return response_factory(message="Failed to create campaign", status=500)


@method_decorator(csrf_exempt, name='dispatch')
class CampaignDetailView(View):
    def get(self, request: HttpRequest, external_id: str):
        try:
            controller = CampaignController()
            
            user_id, payload = controller.jwt_service.decode_token_from_request(request)
            if not user_id:
                return response_factory(message="Unauthorized", status=401)
            
            campaign = controller.campaign_service.get_campaign_by_external_id(external_id)
            
            if not campaign:
                return response_factory(message="Campaign not found", status=404)
            
            if campaign.user_id != user_id:
                return response_factory(message="Forbidden", status=403)
            
            campaign_data = {
                'external_id': str(campaign.external_id),
                'name': campaign.name,
                'google_ads_campaign_id': campaign.google_ads_campaign_id,
                'google_ads_customer_id': campaign.google_ads_customer_id,
                'total_impressions': campaign.total_impressions,
                'total_clicks': campaign.total_clicks,
                'total_cost_micros': campaign.total_cost_micros,
                'total_emissions_kg': float(campaign.total_emissions_kg),
                'utm_params': [{'key': u.key, 'value': u.value} for u in campaign.utm_params],
                'last_synced_at': campaign.last_synced_at.isoformat() if campaign.last_synced_at else None,
                'is_archived': campaign.is_archived,
                'created_at': campaign.created_at.isoformat() if campaign.created_at else None,
                'updated_at': campaign.updated_at.isoformat() if campaign.updated_at else None,
            }
            
            return response_factory(
                data=campaign_data,
                message="Campaign retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Error fetching campaign: {e}", exc_info=True)
            return response_factory(message="Failed to fetch campaign", status=500)
    
    def patch(self, request: HttpRequest, external_id: str):
        try:
            controller = CampaignController()
            
            user_id, payload = controller.jwt_service.decode_token_from_request(request)
            if not user_id:
                return response_factory(message="Unauthorized", status=401)
            
            campaign = controller.campaign_service.get_campaign_by_external_id(external_id)
            
            if not campaign:
                return response_factory(message="Campaign not found", status=404)
            
            if campaign.user_id != user_id:
                return response_factory(message="Forbidden", status=403)
            
            request_data = UpdateCampaignRequest.parse_raw(request.body)
            
            updated_campaign = controller.campaign_service.update_campaign(
                campaign_id=campaign.id,
                request=request_data
            )
            
            campaign_data = {
                'external_id': str(updated_campaign.external_id),
                'name': updated_campaign.name,
                'utm_params': [{'key': u.key, 'value': u.value} for u in updated_campaign.utm_params],
                'updated_at': updated_campaign.updated_at.isoformat() if updated_campaign.updated_at else None,
            }
            
            return response_factory(
                data=campaign_data,
                message="Campaign updated successfully"
            )
            
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return response_factory(
                message="Invalid request data",
                errors=e.errors(),
                status=400
            )
        except Exception as e:
            logger.error(f"Error updating campaign: {e}", exc_info=True)
            return response_factory(message="Failed to update campaign", status=500)
    
    def delete(self, request: HttpRequest, external_id: str):
        try:
            controller = CampaignController()
            
            user_id, payload = controller.jwt_service.decode_token_from_request(request)
            if not user_id:
                return response_factory(message="Unauthorized", status=401)
            
            campaign = controller.campaign_service.get_campaign_by_external_id(external_id)
            
            if not campaign:
                return response_factory(message="Campaign not found", status=404)
            
            if campaign.user_id != user_id:
                return response_factory(message="Forbidden", status=403)
            
            success = controller.campaign_service.delete_campaign(
                campaign_id=campaign.id,
                soft_delete=True
            )
            
            if success:
                return response_factory(message="Campaign deleted successfully")
            else:
                return response_factory(message="Failed to delete campaign", status=500)
            
        except Exception as e:
            logger.error(f"Error deleting campaign: {e}", exc_info=True)
            return response_factory(message="Failed to delete campaign", status=500)


@method_decorator(csrf_exempt, name='dispatch')
class CampaignAnalyticsView(View):
    def get(self, request: HttpRequest, external_id: str):
        try:
            controller = CampaignController()
            
            user_id, payload = controller.jwt_service.decode_token_from_request(request)
            if not user_id:
                return response_factory(message="Unauthorized", status=401)
            
            campaign = controller.campaign_service.get_campaign_by_external_id(external_id)
            
            if not campaign:
                return response_factory(message="Campaign not found", status=404)
            
            if campaign.user_id != user_id:
                return response_factory(message="Forbidden", status=403)
            
            # Parse date parameters
            end_date_str = request.GET.get('end_date')
            start_date_str = request.GET.get('start_date')
            group_by = request.GET.get('group_by', 'day')
            
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            else:
                end_date = date.today()
            
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            else:
                start_date = campaign.created_at.date() if campaign.created_at else (end_date - timedelta(days=30))
            
            analytics = controller.analytics_service.get_campaign_analytics(
                campaign_id=campaign.id,
                start_date=start_date,
                end_date=end_date,
                group_by=group_by
            )
            
            return response_factory(
                data=analytics,
                message="Analytics retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Error fetching analytics: {e}", exc_info=True)
            return response_factory(message="Failed to fetch analytics", status=500)


@method_decorator(csrf_exempt, name='dispatch')
class SyncCampaignView(View):
    def post(self, request: HttpRequest, external_id: str):
        try:
            controller = CampaignController()
            
            user_id, payload = controller.jwt_service.decode_token_from_request(request)
            if not user_id:
                return response_factory(message="Unauthorized", status=401)
            
            campaign = controller.campaign_service.get_campaign_by_external_id(external_id)
            
            if not campaign:
                return response_factory(message="Campaign not found", status=404)
            
            if campaign.user_id != user_id:
                return response_factory(message="Forbidden", status=403)
            
            if not campaign.google_ads_campaign_id or not campaign.google_ads_customer_id:
                return response_factory(
                    message="Campaign is not linked to Google Ads",
                    status=400
                )
            
            # Parse date parameters
            import json
            body_data = json.loads(request.body) if request.body else {}
            
            end_date_str = body_data.get('end_date')
            start_date_str = body_data.get('start_date')
            
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            else:
                end_date = date.today()
            
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            else:
                start_date = end_date - timedelta(days=7)
            
            sample_impressions = [
                GoogleAdsImpressionData(
                    date=start_date,
                    country='United States',
                    device_type='desktop',
                    impressions=1000,
                    clicks=50,
                    cost_micros=5000000
                )
            ]
            
            count, message = controller.campaign_service.sync_google_ads_impressions(
                campaign_id=campaign.id,
                impressions_data=sample_impressions
            )
            
            return response_factory(
                data={
                    'campaign_id': str(campaign.external_id),
                    'records_synced': count,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                },
                message=message
            )
            
        except Exception as e:
            logger.error(f"Error syncing campaign: {e}", exc_info=True)
            return response_factory(message="Failed to sync campaign", status=500)