from core.services.carbon_accounting import CarbonAccountingService
from core.services.event_dispatcher import EventDispatcher
from core.services.session_service import SessionService
from core.services.event_queue import EventQueueService
from core.services.apikey_service import APIKeyService
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponse
from core.db.events import ProcessedEventData
from core.db.carbon import CarbonData
from rest_framework import status
from typing import Dict, Any, List
from django.views import View
import logging
import json

logger = logging.getLogger(__name__)

SDK_EVENT_TYPES = ['page_view', 'conversion', 'ping', 'click']

# def process_events_sync(events_data: List[Dict[str, Any]], api_key_obj) -> Dict[str, Any]:
#     from decimal import Decimal
#     processed_event_data = ProcessedEventData()
#     carbon_service = CarbonAccountingService()
#     carbon_data = CarbonData()
#     session_service = SessionService()
#     dispatcher = EventDispatcher()
    
#     logger.info(f"Processing {len(events_data)} events synchronously")

#     processed_count = 0
#     skipped_count = 0
#     failed_count = 0
    
#     for event in events_data:
#         try:
#             event_type = event['event_type']
#             payload = event['payload']
#             user_id = event['user_id']

#             processor = dispatcher.get_processor(event_type)
#             if not processor:
#                 logger.error(f"No processor for {event_type}")
#                 failed_count += 1
#                 continue

#             result = processor.process(payload)

#             if processed_event_data.is_processed(
#                 result.reference_id,
#                 result.reference_type
#             ):
#                 logger.info(f"Event already processed: {result.reference_id}")
#                 skipped_count += 1
#                 continue

#             processed_event_data.mark_processed(
#                 reference_id=result.reference_id,
#                 reference_type=result.reference_type,
#                 user_id=user_id,
#                 event_type=event_type,
#                 kg_co2_emitted=result.kg_co2_emitted,
#                 metadata=result.metadata
#             )

#             balance = carbon_data.get_balance(user_id)
            
#             emission_amount = result.kg_co2_emitted
#             if not isinstance(emission_amount, Decimal):
#                 emission_amount = Decimal(str(emission_amount))
            
#             transaction = carbon_service.record_emission(
#                 balance=balance,
#                 amount_kg=emission_amount,
#                 reference_id=result.reference_id,
#                 metadata=result.metadata
#             )
            
#             carbon_data.save_transaction(transaction)
#             carbon_data.save_balance(balance)
            
#             session_service.update_or_create(payload, api_key_obj, float(emission_amount))

#             processed_count += 1
#             logger.info(f"Processed {event_type}: {emission_amount}kg CO2e for user {user_id}")

#         except Exception as e:
#             logger.error(f"Failed to process event: {e}", exc_info=True)
#             failed_count += 1
#             continue
#     logger.info(
#         f"Sync processing complete: {processed_count} processed, "
#         f"{skipped_count} skipped, {failed_count} failed"
#     )
#     return {
#         'status': 'completed',
#         'processed': processed_count,
#         'skipped': skipped_count,
#         'failed': failed_count
#     }

@method_decorator(csrf_exempt, name='dispatch')
class EventCollectorView(View):
    def post(self, request):
        try:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse(
                    {'error': 'Invalid JSON'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            api_key = (
                request.headers.get('X-Tracker-Token') or
                data.get('api_key') or 
                data.get('tracker_token') or
                request.GET.get('api_key')
            )
            
            if not api_key:
                return JsonResponse(
                    {'error': 'API key required'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            apikey_service = APIKeyService()
            api_key_obj = apikey_service.validate_api_key(api_key)
            
            if not api_key_obj:
                return JsonResponse(
                    {'error': 'Invalid or inactive API key'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            industry = api_key_obj.industry_category or 'internet'
            product = api_key_obj.product or 'web'
            domain_event_type = f"{industry}_{product}"
            
            dispatcher = EventDispatcher()
            processor = dispatcher.get_processor(domain_event_type)
            
            if not processor:
                return JsonResponse(
                    {
                        'error': f'Unknown domain: {domain_event_type}',
                        'supported_domains': dispatcher.list_supported_events()
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            queue_service = EventQueueService()
            events = data.get('events')
            
            try:
                if events:
                    validated_events = self._validate_batch(events, processor, domain_event_type, api_key_obj, api_key)
                    result = queue_service.queue_events_batch(api_key_obj.user_id, validated_events, api_key)
                else:
                    validated_payload = processor.validate_payload(data)
                    result = queue_service.queue_event(api_key_obj.user_id, domain_event_type, validated_payload, api_key)

                apikey_service.record_usage(api_key_obj)
                
                return JsonResponse({
                    'status': 'queued',
                    'message': 'Events have been queued for processing',
                    'batch_id': result.get('batch_id'),
                    'event_count': len(result.get('events', []))
                }, status=status.HTTP_202_ACCEPTED)
                
            except Exception as queue_error:
                logger.error(f"Queue service unavailable: {queue_error}", exc_info=True)
                return JsonResponse({
                    'error': 'Event queue service is currently unavailable',
                    'message': 'Please ensure LocalStack/SQS and Celery worker are running',
                    'details': str(queue_error)
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        except Exception as e:
            logger.error(f"Event collection error: {e}", exc_info=True)
            return JsonResponse({
                'error': 'Internal server error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _validate_batch(self, events, processor, domain_event_type, api_key_obj, api_key):
        validated_events = []
        for event in events:
            try:
                validated_payload = processor.validate_payload(event)
                validated_events.append({
                    'event_type': domain_event_type,
                    'payload': validated_payload,
                    'api_key': api_key,
                    'user_id': api_key_obj.user_id,
                    'industry_category': api_key_obj.industry_category,
                    'product': api_key_obj.product
                })
            except Exception as e:
                logger.error(f"Event validation failed: {e}")
                continue
        return validated_events


@method_decorator(csrf_exempt, name='dispatch')
class SupportedEventsView(View):
    def get(self, request):
        dispatcher = EventDispatcher()
        return JsonResponse({
            'supported_domains': dispatcher.list_supported_events(),
            'sdk_event_types': SDK_EVENT_TYPES,
            'total_domains': len(dispatcher.list_supported_events())
        })