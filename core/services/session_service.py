from typing import Dict, Any
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class SessionService:
    def update_or_create(self, payload: dict, api_key_obj, emissions_kg: float):
        from apps.event.models import Session
        from apps.apikey.models import APIKey
        
        session_id = payload.get('session_id')
        if not session_id:
            return None
        
        try:
            api_key_instance = APIKey.objects.get(key=api_key_obj.key)
            
            event_type = payload.get('event', 'page_view')
            utm_params = payload.get('utm_params', {})
            user_agent = payload.get('user_agent') or 'Unknown'
            device_type = self._detect_device_type(user_agent)
            
            session, created = Session.objects.get_or_create(
                session_id=session_id,
                api_key=api_key_instance,
                defaults={
                    'user_id': api_key_obj.user_id,
                    'first_event': timezone.now(),
                    'last_event': timezone.now(),
                    'status': Session.SessionStatus.ACTIVE,
                    'event_count': 0,
                    'utm_params': utm_params,
                    'utm_id': utm_params.get('utm_id', ''),
                    'campaign_id': utm_params.get('utm_campaign', ''),
                    'user_agent': user_agent,
                    'device_type': device_type,
                    'total_emissions_g': 0.0,
                    'events_summary': {},
                    'emissions_breakdown': {}
                }
            )
            
            self._update_metrics(session, event_type, emissions_kg)
            
            logger.info(
                f"Session {session_id} updated: "
                f"{session.event_count} events, {session.total_emissions_g}g CO2e"
            )
            
            return session
            
        except APIKey.DoesNotExist:
            logger.error(f"API key not found: {api_key_obj.key}")
            return None
        except Exception as e:
            logger.error(f"Failed to update session: {e}", exc_info=True)
            return None
    
    def _detect_device_type(self, user_agent: str) -> str:
        if not user_agent or user_agent == 'Unknown':
            return 'desktop'
        
        ua_lower = user_agent.lower()
        if 'mobile' in ua_lower or 'android' in ua_lower:
            return 'mobile'
        elif 'tablet' in ua_lower or 'ipad' in ua_lower:
            return 'tablet'
        return 'desktop'
    
    def _update_metrics(self, session, event_type: str, emissions_kg: float):
        session.last_event = timezone.now()
        session.event_count += 1
        session.total_emissions_g += (emissions_kg * 1000)
        
        events_summary = session.events_summary or {}
        events_summary[event_type] = events_summary.get(event_type, 0) + 1
        session.events_summary = events_summary

        if event_type == 'conversion' and not session.conversion_event:
            session.conversion_event = timezone.now()
        
        emissions_breakdown = session.emissions_breakdown or {}
        emissions_breakdown[event_type] = (
            emissions_breakdown.get(event_type, 0) + (emissions_kg * 1000)
        )
        session.emissions_breakdown = emissions_breakdown
        
        session.save()