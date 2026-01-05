import logging
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from core.services.apikey_service import APIKeyService, ConversionRuleService

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class APIKeyConfigView(View):
    def get(self, request):
        try:
            api_key = request.GET.get('api_key') or request.GET.get('tracker_token')
            
            if not api_key:
                return JsonResponse(
                    {
                        'success': False,
                        'error': 'API key is required',
                        'tracking_enabled': False
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            api_key = api_key.rstrip('/')
            
            apikey_service = APIKeyService()
            api_key_obj = apikey_service.validate_api_key(api_key)
            
            if not api_key_obj:
                return JsonResponse(
                    {
                        'success': False,
                        'error': 'Invalid or inactive API key',
                        'tracking_enabled': False
                    },
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            conversion_service = ConversionRuleService()
            rules = conversion_service.get_api_key_rules(
                api_key_obj.id,
                active_only=True
            )
            
            conversion_rules = [
                {
                    'id': rule.id,
                    'name': rule.name,
                    'rule_type': rule.rule_type,
                    'url_pattern': rule.url_pattern,
                    'match_type': rule.match_type,
                    'css_selector': rule.css_selector,
                    'element_text': rule.element_text,
                    'form_id': rule.form_id,
                    'custom_event_name': rule.custom_event_name,
                    'track_value': rule.track_value,
                    'value_selector': rule.value_selector,
                    'default_value': float(rule.default_value) if rule.default_value else None,
                    'priority': rule.priority
                }
                for rule in rules
            ]
            
            apikey_service.record_usage(api_key_obj)

            industry_type = getattr(api_key_obj, 'industry_type', None) or 'internet';
            product = getattr(api_key_obj,'product',None);
            
            return JsonResponse({
                'success': True,
                'tracking_enabled': api_key_obj.is_active,
                'domain': api_key_obj.domain,
                'industry_type': industry_type,
                'product':product,
                'conversion_rules': conversion_rules,
                'total_rules': len(conversion_rules)
            })
            
        except Exception as e:
            logger.error(f"Error fetching API key config: {e}", exc_info=True)
            return JsonResponse(
                {
                    'success': False,
                    'error': 'Internal server error',
                    'tracking_enabled': False
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )