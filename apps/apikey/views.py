import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from pydantic import ValidationError
from decimal import Decimal
from apps.auth.permissions import IsAuthenticated
from apps.common.response import response_factory
from .models import APIKey, ConversionRule
from .schemas import (
    CreateAPIKeyRequest, APIKeyResponse, APIKeyDetailResponse,
    CreateConversionRuleRequest, UpdateConversionRuleRequest, ConversionRuleResponse,
    VerifyInstallationRequest, VerificationResponse
)
from .services.apikey_service import APIKeyService
from .services.verification_service import ScriptVerificationService

logger = logging.getLogger(__name__)

class APIKeyView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            api_keys = APIKeyService.get_user_api_keys(user)
            
            api_keys_data = [
                APIKeyResponse(
                    id=str(key.external_id),
                    name=key.name,
                    prefix=key.key[:8],
                    domain=key.domain,
                    is_active=key.is_active,
                    last_used_at=key.last_used_at.isoformat() if key.last_used_at else None,
                    created_at=key.created_at.isoformat(),
                    conversion_rules_count=key.conversion_rules.filter(is_active=True).count()
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
                errors={'detail': str(e)},
                status=500
            )
    
    def post(self, request):
        try:
            request_data = CreateAPIKeyRequest(**request.data)
            user = request.user
            
            existing = APIKey.objects.filter(
                user_id=str(user.id),
                name=request_data.name
            ).first()
            
            if existing:
                return response_factory(
                    message="An API key with this name already exists",
                    status=400
                )
            
            api_key = APIKeyService.create_api_key(
                user=user,
                name=request_data.name,
                domain=request_data.domain
            )
            
            response_data = APIKeyDetailResponse(
                id=str(api_key.external_id),
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
        except ValidationError as e:
            return response_factory(
                message="Validation failed",
                errors=e.errors(),
                status=400
            )
        except Exception as e:
            logger.error(f"Error creating API key: {e}", exc_info=True)
            return response_factory(
                message="Failed to create API key",
                errors={'detail': str(e)},
                status=500
            )


class APIKeyDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, key_id):
        try:
            user = request.user
            api_key = APIKeyService.get_api_key_by_id(key_id, user)
            
            if not api_key:
                return response_factory(
                    message="API key not found",
                    status=404
                )
            
            APIKeyService.delete_api_key(api_key)
            
            return response_factory(
                message="API key deleted successfully"
            )
        except Exception as e:
            logger.error(f"Error deleting API key: {e}", exc_info=True)
            return response_factory(
                message="Failed to delete API key",
                errors={'detail': str(e)},
                status=500
            )
    
    def patch(self, request, key_id):
        try:
            user = request.user
            api_key = APIKeyService.get_api_key_by_id(key_id, user)
            
            if not api_key:
                return response_factory(
                    message="API key not found",
                    status=404
                )
            
            api_key = APIKeyService.toggle_api_key(api_key)
            
            return response_factory(
                data={'is_active': api_key.is_active},
                message=f"API key {'activated' if api_key.is_active else 'deactivated'} successfully"
            )
        except Exception as e:
            logger.error(f"Error toggling API key: {e}", exc_info=True)
            return response_factory(
                message="Failed to toggle API key",
                errors={'detail': str(e)},
                status=500
            )


class ConversionRulesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, key_id):
        try:
            user = request.user
            api_key = APIKeyService.get_api_key_by_id(key_id, user)
            
            if not api_key:
                return response_factory(
                    message="API key not found",
                    status=404
                )
            
            rules = ConversionRule.objects.filter(api_key=api_key).order_by('-priority', '-created_at')
            
            rules_data = []
            for rule in rules:
                rule_dict = ConversionRuleResponse(
                    id=str(rule.external_id),
                    name=rule.name,
                    rule_type=rule.rule_type,
                    priority=rule.priority,
                    is_active=rule.is_active,
                    conversion_count=rule.conversion_count,
                    last_triggered_at=rule.last_triggered_at.isoformat() if rule.last_triggered_at else None,
                    created_at=rule.created_at.isoformat(),
                    url_pattern=rule.url_pattern,
                    match_type=rule.match_type,
                    css_selector=rule.css_selector,
                    element_text=rule.element_text,
                    form_id=rule.form_id,
                    custom_event_name=rule.custom_event_name,
                    track_value=rule.track_value if rule.track_value else None,
                    value_selector=rule.value_selector,
                    default_value=float(rule.default_value) if rule.default_value else None
                ).dict(exclude_none=True)
                
                rules_data.append(rule_dict)
            
            return response_factory(
                data={'rules': rules_data, 'total_count': len(rules_data)},
                message="Conversion rules retrieved successfully"
            )
        except Exception as e:
            logger.error(f"Error fetching conversion rules: {e}", exc_info=True)
            return response_factory(
                message="Failed to fetch conversion rules",
                errors={'detail': str(e)},
                status=500
            )
    
    def post(self, request, key_id):
        try:
            user = request.user
            api_key = APIKeyService.get_api_key_by_id(key_id, user)
            
            if not api_key:
                return response_factory(
                    message="API key not found",
                    status=404
                )
            
            request_data = CreateConversionRuleRequest(**request.data)
            
            rule = ConversionRule.objects.create(
                api_key=api_key,
                name=request_data.name,
                rule_type=request_data.rule_type,
                url_pattern=request_data.url_pattern,
                match_type=request_data.match_type,
                css_selector=request_data.css_selector,
                element_text=request_data.element_text,
                form_id=request_data.form_id,
                custom_event_name=request_data.custom_event_name,
                track_value=request_data.track_value,
                value_selector=request_data.value_selector,
                default_value=request_data.default_value,
                priority=request_data.priority,
                is_active=True
            )
            
            return response_factory(
                data={
                    'rule': {
                        'id': str(rule.external_id),
                        'name': rule.name,
                        'rule_type': rule.rule_type,
                        'priority': rule.priority,
                        'is_active': rule.is_active,
                        'created_at': rule.created_at.isoformat()
                    }
                },
                message="Conversion rule created successfully"
            )
        except ValidationError as e:
            return response_factory(
                message="Validation failed",
                errors=e.errors(),
                status=400
            )
        except Exception as e:
            logger.error(f"Error creating conversion rule: {e}", exc_info=True)
            return response_factory(
                message="Failed to create conversion rule",
                errors={'detail': str(e)},
                status=500
            )


class ConversionRuleDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, key_id, rule_id):
        try:
            user = request.user
            api_key = APIKeyService.get_api_key_by_id(key_id, user)
            
            if not api_key:
                return response_factory(
                    message="API key not found",
                    status=404
                )
            
            rule = ConversionRule.objects.filter(
                external_id=rule_id,
                api_key=api_key
            ).first()
            
            if not rule:
                return response_factory(
                    message="Conversion rule not found",
                    status=404
                )
            
            request_data = UpdateConversionRuleRequest(**request.data)
            
            update_fields = ['updated_at']
            if request_data.name is not None:
                rule.name = request_data.name
                update_fields.append('name')
            if request_data.is_active is not None:
                rule.is_active = request_data.is_active
                update_fields.append('is_active')
            if request_data.priority is not None:
                rule.priority = request_data.priority
                update_fields.append('priority')
            if request_data.url_pattern is not None:
                rule.url_pattern = request_data.url_pattern
                update_fields.append('url_pattern')
            if request_data.match_type is not None:
                rule.match_type = request_data.match_type
                update_fields.append('match_type')
            if request_data.css_selector is not None:
                rule.css_selector = request_data.css_selector
                update_fields.append('css_selector')
            if request_data.element_text is not None:
                rule.element_text = request_data.element_text
                update_fields.append('element_text')
            
            rule.save(update_fields=update_fields)
            
            return response_factory(
                data={
                    'rule': {
                        'id': str(rule.external_id),
                        'name': rule.name,
                        'is_active': rule.is_active,
                        'priority': rule.priority
                    }
                },
                message="Conversion rule updated successfully"
            )
        except ValidationError as e:
            return response_factory(
                message="Validation failed",
                errors=e.errors(),
                status=400
            )
        except Exception as e:
            logger.error(f"Error updating conversion rule: {e}", exc_info=True)
            return response_factory(
                message="Failed to update conversion rule",
                errors={'detail': str(e)},
                status=500
            )
    
    def delete(self, request, key_id, rule_id):
        try:
            user = request.user
            api_key = APIKeyService.get_api_key_by_id(key_id, user)
            
            if not api_key:
                return response_factory(
                    message="API key not found",
                    status=404
                )
            
            rule = ConversionRule.objects.filter(
                external_id=rule_id,
                api_key=api_key
            ).first()
            
            if not rule:
                return response_factory(
                    message="Conversion rule not found",
                    status=404
                )
            
            rule.delete()
            
            return response_factory(
                message="Conversion rule deleted successfully"
            )
        except Exception as e:
            logger.error(f"Error deleting conversion rule: {e}", exc_info=True)
            return response_factory(
                message="Failed to delete conversion rule",
                errors={'detail': str(e)},
                status=500
            )


class APIKeyVerificationView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, key_id):
        try:
            user = request.user
            request_data = VerifyInstallationRequest(**request.data)
            
            api_key = APIKeyService.get_api_key_by_id(key_id, user)
            
            if not api_key:
                return response_factory(
                    message="API key not found",
                    status=404
                )
            
            verification_result = ScriptVerificationService.verify_installation(
                url=request_data.url,
                api_key=api_key.key
            )
            
            if not verification_result.get('installed'):
                verification_result['installation_guide'] = ScriptVerificationService.get_installation_instructions(
                    api_key=api_key.key,
                    domain=api_key.domain
                )
            
            return response_factory(
                data=verification_result,
                message="Verification completed"
            )
        except ValidationError as e:
            return response_factory(
                message="Validation failed",
                errors=e.errors(),
                status=400
            )
        except Exception as e:
            logger.error(f"Error verifying SDK installation: {e}", exc_info=True)
            return response_factory(
                message="Failed to verify SDK installation",
                errors={'detail': str(e)},
                status=500
            )


class APIKeyInstallationGuideView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, key_id):
        try:
            user = request.user
            api_key = APIKeyService.get_api_key_by_id(key_id, user)
            
            if not api_key:
                return response_factory(
                    message="API key not found",
                    status=404
                )
            
            instructions = ScriptVerificationService.get_installation_instructions(
                api_key=api_key.key,
                domain=api_key.domain
            )
            
            return response_factory(
                data={
                    'api_key': {
                        'id': str(api_key.external_id),
                        'name': api_key.name,
                        'domain': api_key.domain,
                        'prefix': api_key.key[:11]
                    },
                    'installation': instructions
                },
                message="Installation instructions retrieved"
            )
        except Exception as e:
            logger.error(f"Error getting installation guide: {e}", exc_info=True)
            return response_factory(
                message="Failed to get installation guide",
                errors={'detail': str(e)},
                status=500
            )


@csrf_exempt
@require_http_methods(["GET"])
def get_conversion_config(request):
    try:
        api_key = request.GET.get('api_key') or request.headers.get('X-API-Key')
        
        if not api_key:
            return JsonResponse({
                'success': False,
                'error': 'API key is required'
            }, status=400)
        
        api_key_obj = APIKeyService.validate_api_key(api_key)
        
        if not api_key_obj:
            return JsonResponse({
                'success': False,
                'error': 'Invalid API key'
            }, status=401)
        
        rules = ConversionRule.objects.filter(
            api_key=api_key_obj,
            is_active=True
        ).order_by('-priority', 'created_at')
        
        conversion_rules = []
        for rule in rules:
            rule_data = {
                'id': str(rule.external_id),
                'type': rule.rule_type,
                'name': rule.name,
                'priority': rule.priority,
            }
            
            if rule.rule_type == 'url':
                rule_data['pattern'] = rule.url_pattern
                rule_data['match_type'] = rule.match_type
            elif rule.rule_type == 'click':
                rule_data['selector'] = rule.css_selector
                if rule.element_text:
                    rule_data['element_text'] = rule.element_text
            elif rule.rule_type == 'form_submit':
                rule_data['form_id'] = rule.form_id
            elif rule.rule_type == 'custom_event':
                rule_data['event_name'] = rule.custom_event_name
            
            if rule.track_value:
                rule_data['track_value'] = True
                rule_data['value_selector'] = rule.value_selector
                rule_data['default_value'] = float(rule.default_value) if rule.default_value else None
            
            conversion_rules.append(rule_data)
        
        return JsonResponse({
            'success': True,
            'conversion_rules': conversion_rules,
            'tracking_enabled': api_key_obj.is_active,
            'total_rules': len(conversion_rules),
            'domain': api_key_obj.domain,
        })
    except Exception as e:
        logger.error(f"Error fetching conversion config: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)