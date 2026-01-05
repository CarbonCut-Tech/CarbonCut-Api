import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from pydantic import ValidationError
from apps.auth.permissions import IsAuthenticated
from apps.common.response import response_factory
from core.services.apikey_service import APIKeyService, ConversionRuleService
from core.services.script_verification import ScriptVerificationService
from apps.apikey.schemas import (
    CreateAPIKeyRequest, APIKeyResponse, APIKeyDetailResponse,
)

logger = logging.getLogger(__name__)

class APIKeyController:
    def __init__(self):
        self.apikey_service = APIKeyService()
        self.conversion_service = ConversionRuleService()
        self.verification_service = ScriptVerificationService()


@method_decorator(csrf_exempt, name='dispatch')
class APIKeyView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            controller = APIKeyController()
            request_data = CreateAPIKeyRequest(**request.data)
            user = request.user

            api_key = controller.apikey_service.create_api_key(
                user_id=str(user.id),
                name=request_data.name,
                domain=request_data.domain,
                industry_category=request_data.industry_category,
                product=request_data.product
            )

            response_data = APIKeyDetailResponse(
                id=api_key.id,
                name=api_key.name,
                domain=api_key.domain,
                is_active=api_key.is_active,
                created_at=api_key.created_at.isoformat(),
                prefix=api_key.key[:11],
                full_key=api_key.key
            ).dict()

            return response_factory(
                data={'api_key': response_data},
                message="API key created successfully"
            )
        except Exception as e:
            logger.error(f"Error creating API key: {e}", exc_info=True)
            return response_factory(
                message="Failed to create API key",
                status=500
            )
    def get(self, request):
        try:
            controller = APIKeyController()
            user = request.user
            
            api_keys = controller.apikey_service.get_user_api_keys(str(user.id))
            
            api_keys_data = [
                APIKeyResponse(
                    id=key.id,
                    name=key.name,
                    prefix=key.key[:8],
                    domain=key.domain,
                    is_active=key.is_active,
                    industry_category=key.industry_category,
                    product=key.product,
                    last_used_at=key.last_used_at.isoformat() if key.last_used_at else None,
                    created_at=key.created_at.isoformat(),
                    conversion_rules_count=len(
                        controller.conversion_service.get_api_key_rules(key.id, active_only=True)
                    )
                ).dict() for key in api_keys
            ]
            
            return response_factory(
                data={'api_keys': api_keys_data},
                message="API keys retrieved successfully"
            )
        except Exception as e:
            logger.error(f"Error fetching API keys: {e}", exc_info=True)
            return response_factory(
                message="Failed to fetch API keys",
                status=500
            )

@method_decorator(csrf_exempt, name='dispatch')
class APIKeyDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, key_id):
        try:
            controller = APIKeyController()
            user = request.user
            
            success = controller.apikey_service.delete_api_key(key_id, str(user.id))
            
            if not success:
                return response_factory(
                    message="API key not found",
                    status=404
                )
            
            return response_factory(message="API key deleted successfully")
            
        except Exception as e:
            logger.error(f"Error deleting API key: {e}", exc_info=True)
            return response_factory(
                message="Failed to delete API key",
                status=500
            )

    def patch(self, request, key_id):
        try:
            controller = APIKeyController()
            user = request.user
            api_key = controller.apikey_service.get_api_key_by_id(key_id, str(user.id))
            if not api_key:
                return response_factory(
                    message="API key not found",
                    status=404
                )
            
            updated_key = controller.apikey_service.toggle_api_key(api_key)
            return response_factory(
                data={
                    'is_active': updated_key.is_active
                },
                message=f"API key {'activated' if updated_key.is_active else 'deactivated'}"
            )
        except Exception as e:
            logger.error(f"Error toggling API key: {e}", exc_info=True)
            return response_factory(
                message="Failed to update API key",
                status=500
            )