import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DeviceService:
    @staticmethod
    def detect_device_type(user_agent: str, screen_resolution: Optional[str] = None) -> str:
        if screen_resolution:
            return DeviceService._detect_from_resolution(screen_resolution, user_agent)
        return DeviceService._detect_from_user_agent(user_agent)
    
    @staticmethod
    def _detect_from_user_agent(user_agent: str) -> str:
        user_agent_lower = user_agent.lower()
        
        if any(kw in user_agent_lower for kw in ['iphone', 'android', 'mobile', 'phone']):
            if 'tablet' not in user_agent_lower and 'ipad' not in user_agent_lower:
                return 'mobile'
        
        if any(kw in user_agent_lower for kw in ['ipad', 'tablet']):
            return 'tablet'
        
        if 'tv' in user_agent_lower or 'smarttv' in user_agent_lower:
            return 'tv'
        
        return 'desktop'
    
    @staticmethod
    def _detect_from_resolution(screen_resolution: str, user_agent: str = '') -> str:
        try:
            if not screen_resolution or 'x' not in screen_resolution:
                return DeviceService._detect_from_user_agent(user_agent)
            
            parts = screen_resolution.lower().split('x')
            if len(parts) != 2:
                return DeviceService._detect_from_user_agent(user_agent)
            
            width = int(parts[0].strip())
            height = int(parts[1].strip())
            
            min_dimension = min(width, height)
            max_dimension = max(width, height)
            
            user_agent_lower = user_agent.lower()
            
            if min_dimension < 768:
                if max_dimension < 900:
                    return 'mobile'
                return 'tablet' if 'ipad' in user_agent_lower or 'tablet' in user_agent_lower else 'mobile'
            
            elif min_dimension < 1024:
                if any(kw in user_agent_lower for kw in ['ipad', 'tablet', 'kindle']):
                    return 'tablet'
                aspect_ratio = max_dimension / min_dimension
                if 1.3 <= aspect_ratio <= 1.8:
                    return 'tablet'
                return 'desktop'
            
            else:
                if min_dimension >= 1920 or max_dimension >= 2560:
                    if 'tv' in user_agent_lower or 'smarttv' in user_agent_lower:
                        return 'tv'
                return 'desktop'
            
        except (ValueError, IndexError, AttributeError) as e:
            logger.warning(f"Error parsing screen resolution '{screen_resolution}': {e}")
            return DeviceService._detect_from_user_agent(user_agent)