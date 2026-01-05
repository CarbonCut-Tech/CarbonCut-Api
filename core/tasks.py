from celery import shared_task
import logging
from typing import Dict, Any, List
import traceback

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_event_batch_task(self, events_data: List[Dict[str, Any]]):
    from core.services.event_dispatcher import EventDispatcher
    from core.services.carbon_accounting import CarbonAccountingService
    from core.services.session_service import SessionService
    from core.services.apikey_service import APIKeyService
    from core.db.carbon import CarbonData
    from core.db.events import ProcessedEventData
    from decimal import Decimal
    # why are we importing here?
    
    try:
        processed_event_data = ProcessedEventData()
        carbon_service = CarbonAccountingService()
        carbon_data = CarbonData()
        session_service = SessionService()
        apikey_service = APIKeyService()
        dispatcher = EventDispatcher()
        
        logger.info(f"[CELERY] Processing {len(events_data)} events asynchronously")
        
        processed_count = 0
        skipped_count = 0
        failed_count = 0
        
        for event in events_data:
            try:
                event_type = event['event_type']
                payload = event['payload']
                user_id = event['user_id']
                # api key should be validated before and org id/user id should be passed here
                api_key = event.get('api_key')

                processor = dispatcher.get_processor(event_type)
                if not processor:
                    logger.error(f"No processor for {event_type}")
                    _log_failed_event(event, f"No processor found for {event_type}")
                    failed_count += 1
                    continue

                result = processor.process(payload)

                if processed_event_data.is_processed(
                    result.reference_id,
                    result.reference_type
                ):
                    logger.info(f"Event already processed: {result.reference_id}")
                    skipped_count += 1
                    continue

                processed_event_data.mark_processed(
                    reference_id=result.reference_id,
                    reference_type=result.reference_type,
                    user_id=user_id,
                    event_type=event_type,
                    kg_co2_emitted=result.kg_co2_emitted,
                    metadata=result.metadata
                )

                balance = carbon_data.get_balance(user_id)
                
                emission_amount = result.kg_co2_emitted
                if not isinstance(emission_amount, Decimal):
                    emission_amount = Decimal(str(emission_amount))
                
                transaction = carbon_service.record_emission(
                    balance=balance,
                    amount_kg=emission_amount,
                    reference_id=result.reference_id,
                    metadata=result.metadata
                )
                
                # what will happen if two events come in parallel?
                # what will happen if save_transaction is successful but save_balance fails?
                carbon_data.save_transaction(transaction)
                carbon_data.save_balance(balance)
                
                if api_key:
                    api_key_obj = apikey_service.validate_api_key(api_key)
                    if api_key_obj:
                        session_service.update_or_create(payload, api_key_obj, float(emission_amount))

                processed_count += 1
                logger.info(f"[CELERY] Processed {event_type}: {emission_amount}kg CO2e for user {user_id}")

            except Exception as e:
                error_msg = str(e)
                error_trace = traceback.format_exc()
                logger.error(f"Failed to process event: {error_msg}", exc_info=True)
                _log_failed_event(event, error_msg, error_trace)
                failed_count += 1
                continue

        logger.info(
            f"[CELERY] Batch complete: {processed_count} processed, "
            f"{skipped_count} skipped, {failed_count} failed"
        )

        return {
            'status': 'completed',
            'processed': processed_count,
            'skipped': skipped_count,
            'failed': failed_count
        }

    except Exception as e:
        logger.error(f"Batch processing error: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)


def _log_failed_event(event: Dict[str, Any], error_msg: str, error_trace: str = ""):
    """Log failed event to database for retry/monitoring"""
    try:
        from apps.event.models import FailedEvent
        
        FailedEvent.objects.create(
            event_type=event.get('event_type', 'unknown'),
            payload=event.get('payload', {}),
            error_message=error_msg,
            error_traceback=error_trace,
            original_queue_message_id=event.get('message_id', ''),
        )
    except Exception as log_error:
        logger.error(f"Failed to log failed event: {log_error}")


@shared_task
def retry_failed_events():
    from apps.event.models import FailedEvent
    from django.utils import timezone
    from datetime import timedelta
    from django.db import models
    
    cutoff_time = timezone.now() - timedelta(minutes=5)
    
    failed_events = FailedEvent.objects.filter(
        status='pending',
        retry_count__lt=models.F('max_retries'),
        last_retry_at__lt=cutoff_time
    ) | FailedEvent.objects.filter(
        status='pending',
        retry_count__lt=models.F('max_retries'),
        last_retry_at__isnull=True
    )
    
    for failed_event in failed_events[:10]:
        try:
            failed_event.status = 'processing'
            failed_event.retry_count += 1
            failed_event.last_retry_at = timezone.now()
            failed_event.save()
            
            event_data = {
                'event_type': failed_event.event_type,
                'payload': failed_event.payload,
                'user_id': failed_event.payload.get('user_id', ''),
            }
            
            process_event_batch_task.delay([event_data])
            
            failed_event.status = 'resolved'
            failed_event.resolved_at = timezone.now()
            failed_event.save()
            
            logger.info(f"Retried failed event {failed_event.id}")
            
        except Exception as e:
            failed_event.status = 'pending'
            failed_event.save()
            logger.error(f"Failed to retry event {failed_event.id}: {e}")
            
            if failed_event.retry_count >= failed_event.max_retries:
                failed_event.status = 'abandoned'
                failed_event.save()


@shared_task
def process_dlq_messages():
    import boto3
    from django.conf import settings
    
    sqs = boto3.client(
        'sqs',
        endpoint_url=settings.AWS_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_DEFAULT_REGION,
    )
    
    # for now
    dlq_url = f"{settings.AWS_ENDPOINT_URL}/000000000000/carbon-events-dlq"
    
    response = sqs.receive_message(
        QueueUrl=dlq_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=1
    )
    
    messages = response.get('Messages', [])
    
    for message in messages:
        try:
            import json
            body = json.loads(message['Body'])
            
            _log_failed_event(
                body,
                "Message from DLQ",
                f"Message ID: {message['MessageId']}"
            )
            
            sqs.delete_message(
                QueueUrl=dlq_url,
                ReceiptHandle=message['ReceiptHandle']
            )
            
        except Exception as e:
            logger.error(f"Failed to process DLQ message: {e}")


@shared_task
def process_active_sessions_task():
    from core.services.session_manager import SessionManager
    
    try:
        session_manager = SessionManager()
        result = session_manager.process_active_sessions()
        
        logger.info(f"Processed {result['processed']} active sessions")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to process active sessions: {e}", exc_info=True)
        raise


@shared_task
def mark_inactive_sessions_task():
    from core.services.session_manager import SessionManager
    
    try:
        session_manager = SessionManager()
        result = session_manager.mark_inactive_sessions()
        
        logger.info(f"Marked {result['marked']} sessions as inactive")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to mark inactive sessions: {e}", exc_info=True)
        raise