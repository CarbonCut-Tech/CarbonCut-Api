from .services.event_validation_service import EventValidationError, EventValidationService
from .services.location_service import LocationService
from apps.apikey.models import  ConversionRule, APIKey  
from .services.device_service import DeviceService
from .services.event_service import EventService
from django.db.models import Sum, F
from django.db import transaction
from django.utils import timezone
from celery import shared_task
from .models import Session
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def handle_event(self, event_data: dict, request_data: dict = None):
    try:
        EventValidationService.validate(event_data)
        
        event_type = event_data.get('event_type')
        session_id = event_data.get('session_id')
        event_time = EventService.parse_event_time(event_data.get('event_time'))
        utm_param = event_data.get('utm_param', {})
        api_key_value = event_data.get('api_key')
        
        try:
            api_key_obj = APIKey.objects.get(key=api_key_value, is_active=True)
        except APIKey.DoesNotExist:
            raise EventValidationError("Invalid API key")
        
        user_agent = request_data.get('user_agent', '') if request_data else event_data.get('user_agent', '')
        ip_address = request_data.get('ip_address', '') if request_data else ''
        location_data = request_data.get('location_data', {}) if request_data else {}
        device_type = request_data.get('device_type', 'desktop') if request_data else event_data.get('device_type', 'desktop')
        extra_data = request_data.get('extra_data', {}) if request_data else {}
        
        latitude = request_data.get('latitude') if request_data else None
        longitude = request_data.get('longitude') if request_data else None
        location_accuracy = request_data.get('location_accuracy') if request_data else None
        location_source = request_data.get('location_source', 'ip_geolocation') if request_data else 'ip_geolocation'
        
        bytes_data = {
            'bytes_per_page_view': extra_data.get('bytesPerPageView', 0),
            'bytes_per_click': extra_data.get('bytesPerClick', 0),
            'bytes_per_conversion': extra_data.get('bytesPerConversion', 0),
            'encoded_size': extra_data.get('encodedSize', 0),
            'decoded_size': extra_data.get('decodedSize', 0),
            'tracking_request_bytes': extra_data.get('trackingRequestBytes', 0),
            'tracking_request_body': extra_data.get('trackingRequestBody', 0),
            'resource_count': extra_data.get('resourceCount', 0),
            'resource_types': extra_data.get('resourceTypes', {}),
        }
        
        event_dict = EventService.build_event_dict(
            event_type=event_type,
            event_time=event_time,
            event_data=event_data,
            user_agent=user_agent,
            ip_address=ip_address,
            utm_param=utm_param,
            location_data=location_data,
            device_type=device_type,
            bytes_data=bytes_data,
            latitude=latitude,
            longitude=longitude,
            screen_resolution=extra_data.get('screen_resolution', '')
        )
        
        session, created = EventService.get_or_create_session(
            session_id=session_id,
            api_key=api_key_obj,
            event_time=event_time,
            event_dict=event_dict,
            utm_param=utm_param,
            location_data=location_data,
            device_type=device_type,
            user_agent=user_agent,
            ip_address=ip_address,
            latitude=latitude,
            longitude=longitude,
            location_accuracy=location_accuracy,
            location_source=location_source
        )
        
        should_schedule_task = created
        
        if not created:
            should_schedule_task = EventService.update_session(
                session=session,
                event_time=event_time,
                event_dict=event_dict,
                event_type=event_type,
                latitude=latitude,
                longitude=longitude,
                location_accuracy=location_accuracy,
                location_source=location_source,
                city=location_data.get('city', ''),
                state=location_data.get('state', '')
            )
        
        if event_type == "conversion":
            _handle_conversion_event(
                api_key_obj=api_key_obj,
                session_id=session_id,
                event_data=event_data,
                extra_data=extra_data,
                utm_param=utm_param,
                user_agent=user_agent,
                ip_address=ip_address,
                location_data=location_data,
                device_type=device_type,
                event_time=event_time
            )
        
        if should_schedule_task:
            process_session_end.apply_async(
                args=[str(session.external_id)],
                countdown=15
            )
            logger.info(f"Scheduled session end task for {session_id}")
        
        return {
            'success': True,
            'message': 'Event processed successfully',
            'session_id': session.session_id,
            'external_id': str(session.external_id),
            'event_type': event_type,
            'utm_id': utm_param.get('utm_id'),
        }
        
    except EventValidationError as e:
        logger.error(f"Event validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error handling event: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=5)


@shared_task
def process_session_end(session_external_id: str):
    try:
        with transaction.atomic():
            session = Session.objects.select_for_update().filter(
                external_id=session_external_id
            ).first()
            
            if not session:
                logger.warning(f"Session {session_external_id} not found")
                return
            
            if session.status in [Session.SessionStatus.PROCESSING, Session.SessionStatus.CLOSED]:
                logger.info(f"Session {session.session_id} is {session.status}, skipping")
                return

            time_since_last_event = timezone.now() - session.last_event
            if time_since_last_event.total_seconds() < 15:
                logger.info(f"Session {session.session_id} still active, rescheduling")
                process_session_end.apply_async(
                    args=[session_external_id],
                    countdown=15
                )
                return
            
            session.status = Session.SessionStatus.PROCESSING
            session.last_processed_at = timezone.now()
            session.save(update_fields=['status', 'last_processed_at', 'updated_at'])
        
        session_duration = (session.last_event - session.first_event).total_seconds()
        
        logger.info(
            f"Processing session end: {session.session_id} | "
            f"Duration: {session_duration}s | Events: {len(session.events or [])}"
        )
        
        try:
            # Calculate emissions (import your emissions service)
            # from apps.accounting.services import AccountingService
            # from apps.campaign.services import CampaignEmissionService
            
            # emissions_result = calculate_session_emissions_sync(session=session)
            # ... your emissions logic here
            
            session.status = Session.SessionStatus.CLOSED
            session.save(update_fields=['status', 'updated_at'])
            logger.info(f"Session {session.session_id} closed successfully")
            
        except Exception as e:
            logger.error(f"Error processing session {session.session_id}: {e}", exc_info=True)
            session.status = Session.SessionStatus.ACTIVE
            session.save(update_fields=['status', 'updated_at'])
            raise
    
    except Exception as e:
        logger.error(f"Error in process_session_end: {e}", exc_info=True)
        raise


def _handle_conversion_event(
    api_key_obj,
    session_id: str,
    event_data: dict,
    extra_data: dict,
    utm_param: dict,
    user_agent: str,
    ip_address: str,
    location_data: dict,
    device_type: str,
    event_time
):
    try:
        conversion_rule = None
        conversion_rule_id = extra_data.get('conversion_rule_id')
        
        if conversion_rule_id:
            conversion_rule = ConversionRule.objects.filter(
                external_id=conversion_rule_id,
                api_key=api_key_obj,
                is_active=True
            ).first()
        
        # existing_conversion = ConversionEvent.objects.filter(
        #     session_id=session_id,
        #     conversion_label=extra_data.get('conversion_label', 'Conversion'),
        #     created_at__gte=event_time - timezone.timedelta(seconds=5)
        # ).exists()
        
        # if not existing_conversion:
        #     conversion_event = ConversionEvent.objects.create(
        #         api_key=api_key_obj,
        #         conversion_rule=conversion_rule,
        #         session_id=session_id,
        #         event_type='conversion',
        #         conversion_label=extra_data.get('conversion_label', 'Conversion'),
        #         conversion_value=extra_data.get('conversion_value'),
        #         currency=extra_data.get('currency', 'USD'),
        #         page_url=event_data.get('page_url', ''),
        #         referrer=event_data.get('referrer', ''),
        #         user_agent=user_agent,
        #         ip_address=ip_address,
        #         country=location_data.get('country', 'United States'),
        #         device_type=device_type,
        #         extras={
        #             'conversion_type': extra_data.get('conversion_type'),
        #             'conversion_url': extra_data.get('conversion_url'),
        #             'match_type': extra_data.get('match_type'),
        #             'pattern': extra_data.get('pattern'),
        #             'utm_params': utm_param,
        #             'utm_id': utm_param.get('utm_id'),
        #             'event_id': event_data.get('event_id'),
        #         }
        #     )
            
        # logger.info(f"Created conversion event {conversion_event.external_id} for session {session_id}")
            
            if conversion_rule:
                ConversionRule.objects.filter(
                    external_id=conversion_rule.external_id
                ).update(
                    conversion_count=F('conversion_count') + 1,
                    last_triggered_at=timezone.now()
                )
        else:
            logger.info(f"Skipped duplicate conversion for session {session_id}")
        
    except Exception as e:
        logger.error(f"Failed to create conversion event: {e}", exc_info=True)