from decimal import Decimal
from datetime import datetime, timedelta

class SessionRules:
    
    TIMEOUT_SECONDS = 1800
    EMISSION_PER_MINUTE = Decimal('0.0001')
    EMISSION_PER_EVENT = Decimal('0.00005')
    MAX_SESSION_DURATION_HOURS = 24
    
    def is_session_timeout(self, last_activity: datetime) -> bool:
        inactive_seconds = (datetime.now() - last_activity).total_seconds()
        return inactive_seconds >= self.TIMEOUT_SECONDS
    
    def calculate_session_emissions(
        self, 
        duration_seconds: float, 
        event_count: int
    ) -> Decimal:
        duration_minutes = Decimal(str(duration_seconds / 60))
        events = Decimal(str(event_count))
        
        total = (
            duration_minutes * self.EMISSION_PER_MINUTE +
            events * self.EMISSION_PER_EVENT
        )
        
        return round(total, 6)
    
    def is_session_too_long(self, duration_seconds: float) -> bool:
        max_seconds = self.MAX_SESSION_DURATION_HOURS * 3600
        return duration_seconds > max_seconds