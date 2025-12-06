import logging
from typing import Dict, Optional
from datetime import datetime
from django.db import transaction

from apps.event.models import Session
from ..models import Campaign, CampaignEmission
from .coefficient_service import CoefficientService
from .traffic_classifier import TrafficClassifier
from .grid_intensity_service import get_grid_intensity_sync

logger = logging.getLogger(__name__)


class EmissionCalculator:
    def __init__(self):
        self.coef_service = CoefficientService()
    
    async def calculate_session_emissions(
        self,
        session: Session,
        campaign: Optional[Campaign] = None
    ) -> Dict[str, float]:
        session_data = self._extract_session_data(session)
        
        utm_params = session_data.get('utm_params', {})
        referrer = session_data.get('referrer', '')
        traffic_type = TrafficClassifier.classify_session(utm_params, referrer, campaign)
        
        logger.info(f"Session {session.session_id} classified as: {traffic_type}")
        
        if TrafficClassifier.is_paid_advertising(traffic_type):
            return await self._calculate_paid_ad_emissions(session, session_data, campaign)
        else:
            return await self._calculate_organic_emissions(session, session_data)
    
    def _extract_session_data(self, session: Session) -> Dict:
        utm_params = {}
        bytes_data = {}
        referrer = ''
        
        if session.events and isinstance(session.events, list) and len(session.events) > 0:
            first_event = session.events[0]
            utm_params = first_event.get('utm_param', {})
            referrer = first_event.get('referrer', '')
            
            latest_event = session.events[-1]
            bytes_data = latest_event.get('bytes_data', {})
        
        return {
            'country': session.country or 'United States',
            'device_type': session.device_type or 'desktop',
            'utm_params': utm_params,
            'referrer': referrer,
            'bytes_data': bytes_data,
            'latitude': session.latitude,
            'longitude': session.longitude,
            'ip_address': session.ip_address,
        }
    
    async def _calculate_paid_ad_emissions(
        self,
        session: Session,
        session_data: Dict,
        campaign: Optional[Campaign]
    ) -> Dict[str, float]:
        platform = self._identify_platform(session_data.get('utm_params', {}))
        traffic_type = 'paid_ads'
        
        page_views = sum(1 for e in session.events if e.get('event_type') == 'page_view')
        clicks = sum(1 for e in session.events if e.get('event_type') == 'click')
        conversions = 1 if session.conversion_event else 0
        
        page_view_emissions_g = await self._calculate_page_view_emissions(
            session, session_data, page_views, traffic_type, platform
        )
        
        click_emissions_g = await self._calculate_click_emissions(
            clicks, session_data, traffic_type, platform
        )
        
        conversion_emissions_g = await self._calculate_conversion_emissions(
            conversions, session_data, traffic_type, platform
        )
        adtech_overhead_g = await self._calculate_adtech_overhead(
            page_views + clicks + conversions,
            session_data,
            platform
        )
        
        total_emissions_g = (
            page_view_emissions_g +
            click_emissions_g +
            conversion_emissions_g +
            adtech_overhead_g
        )
        
        return {
            'page_view_emissions_g': page_view_emissions_g,
            'click_emissions_g': click_emissions_g,
            'conversion_emissions_g': conversion_emissions_g,
            'adtech_overhead_g': adtech_overhead_g,
            'total_emissions_g': total_emissions_g,
            'traffic_type': traffic_type,
            'platform': platform,
        }
    
    async def _calculate_organic_emissions(
        self,
        session: Session,
        session_data: Dict
    ) -> Dict[str, float]:
        """Calculate emissions for organic traffic"""
        traffic_type = 'organic'

        page_views = sum(1 for e in session.events if e.get('event_type') == 'page_view')
        clicks = sum(1 for e in session.events if e.get('event_type') == 'click')
        conversions = 1 if session.conversion_event else 0
        
        page_view_emissions_g = await self._calculate_page_view_emissions(
            session, session_data, page_views, traffic_type, platform=None
        )
        
        click_emissions_g = await self._calculate_click_emissions(
            clicks, session_data, traffic_type, platform=None
        )
        
        conversion_emissions_g = await self._calculate_conversion_emissions(
            conversions, session_data, traffic_type, platform=None
        )
        
        total_emissions_g = (
            page_view_emissions_g +
            click_emissions_g +
            conversion_emissions_g
        )
        
        return {
            'page_view_emissions_g': page_view_emissions_g,
            'click_emissions_g': click_emissions_g,
            'conversion_emissions_g': conversion_emissions_g,
            'adtech_overhead_g': 0.0,  
            'traffic_type': traffic_type,
            'platform': None,
        }
    
    async def _calculate_page_view_emissions(
        self,
        session: Session,
        session_data: Dict,
        page_views: int,
        traffic_type: str,
        platform: Optional[str]
    ) -> float:
        if page_views == 0:
            return 0.0
        
        device_type = session_data['device_type']
        country = session_data['country']
        bytes_data = session_data.get('bytes_data', {})
        
        # 1. Get bytes transferred
        total_bytes = self._get_page_bytes(bytes_data, device_type, traffic_type)
        
        # 2. Get grid intensity (REAL-TIME)
        grid_result = await self._get_grid_intensity(country)
        grid_intensity = grid_result['currentHourIntensity']  # g CO2/kWh
        ef_geo = grid_intensity / 1000  # kg CO2/kWh
        
        # 3. Network emissions
        network_energy_per_mb = self.coef_service.get_network_energy(traffic_type=traffic_type)
        total_mb = total_bytes / (1024 * 1024)
        network_energy_kwh = page_views * total_mb * network_energy_per_mb * 1e-3
        network_emissions_g = network_energy_kwh * ef_geo * 1000
        
        # 4. Device emissions
        device_power_w = self.coef_service.get_device_power(device_type, traffic_type)
        view_time_hours = 0.0083  
        device_energy_kwh = page_views * (device_power_w * view_time_hours) * 1e-3
        device_emissions_g = device_energy_kwh * ef_geo * 1000
        
        logger.debug(
            f"Page view: {page_views}x, {total_bytes/1024:.1f}KB, "
            f"grid={grid_intensity}g, network={network_emissions_g:.2f}g, "
            f"device={device_emissions_g:.2f}g"
        )
        
        return network_emissions_g + device_emissions_g
    
    async def _calculate_click_emissions(
        self,
        clicks: int,
        session_data: Dict,
        traffic_type: str,
        platform: Optional[str]
    ) -> float:
        if clicks == 0:
            return 0.0
        
        click_energy_wh = self.coef_service.get_coefficient(
            name='click_energy_per_event',
            component='network',
            traffic_type=traffic_type,
            platform=platform
        ) or 0.1
        
        country = session_data['country']
        grid_result = await self._get_grid_intensity(country)
        ef_geo = grid_result['currentHourIntensity'] / 1000
        
        total_energy_kwh = clicks * click_energy_wh * 1e-3
        return total_energy_kwh * ef_geo * 1000
    
    async def _calculate_conversion_emissions(
        self,
        conversions: int,
        session_data: Dict,
        traffic_type: str,
        platform: Optional[str]
    ) -> float:
        if conversions == 0:
            return 0.0
        
        conversion_energy_wh = self.coef_service.get_coefficient(
            name='conversion_energy_per_event',
            component='server',
            traffic_type=traffic_type,
            platform=platform
        ) or 2.0
        
        country = session_data['country']
        grid_result = await self._get_grid_intensity(country)
        ef_geo = grid_result['currentHourIntensity'] / 1000
        
        total_energy_kwh = conversions * conversion_energy_wh * 1e-3
        return total_energy_kwh * ef_geo * 1000
    
    async def _calculate_adtech_overhead(
        self,
        total_events: int,
        session_data: Dict,
        platform: Optional[str]
    ) -> float:
        if total_events == 0:
            return 0.0
        
        adtech_energy_wh = self.coef_service.get_adtech_energy(platform)
        
        country = session_data['country']
        grid_result = await self._get_grid_intensity(country)
        ef_geo = grid_result['currentHourIntensity'] / 1000
        
        total_energy_kwh = total_events * adtech_energy_wh * 1e-3
        return total_energy_kwh * ef_geo * 1000
    
    def _get_page_bytes(self, bytes_data: Dict, device_type: str, traffic_type: str) -> int:
        encoded = bytes_data.get('encodedBodySize', 0)
        decoded = bytes_data.get('decodedBodySize', 0)
        
        if encoded > 0:
            return encoded
        elif decoded > 0:
            return decoded
        else:
            estimated_bytes = self.coef_service.get_coefficient(
                name='default_page_size_bytes',
                component='network',
                traffic_type=traffic_type,
                device_type=device_type
            )
            return int(estimated_bytes) if estimated_bytes else (1.5 * 1024 * 1024)
    
    async def _get_grid_intensity(self, country: str) -> Dict[str, float]:
        return get_grid_intensity_sync(country)
    
    def _identify_platform(self, utm_params: Dict) -> Optional[str]:
        utm_source = utm_params.get('utm_source', '').lower()
        
        platform_mapping = {
            'google': 'google_ads',
            'facebook': 'facebook_ads',
            'linkedin': 'linkedin_ads',
            'twitter': 'twitter_ads',
            'instagram': 'instagram_ads',
            'tiktok': 'tiktok_ads',
            'pinterest': 'pinterest_ads',
            'snapchat': 'snapchat_ads',
        }
        
        return platform_mapping.get(utm_source)