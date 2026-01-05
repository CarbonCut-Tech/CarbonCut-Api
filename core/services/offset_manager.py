from decimal import Decimal
from ..models.carbon_account import CarbonOffset

class OffsetManager:
    
    def create_offset(
        self,
        user_id: str,
        amount_kg: Decimal,
        price_per_kg: Decimal,
        provider: str,
        certificate_id: str,
        metadata: dict = None
    ) -> CarbonOffset:
        
        if amount_kg <= 0:
            raise ValueError("Offset amount must be positive")
        
        if price_per_kg <= 0:
            raise ValueError("Price per kg must be positive")
        
        offset = CarbonOffset(
            user_id=user_id,
            amount_kg=amount_kg,
            price_per_kg=price_per_kg,
            provider=provider,
            certificate_id=certificate_id,
            status='completed',
            metadata=metadata or {}
        )
        
        return offset
    
    def validate_provider(self, provider: str) -> bool:
        valid_providers = [
            'GreenCarbon Inc',
            'EcoOffset Ltd',
            'ClimateAction',
            'CarbonNeutral'
        ]
        return provider in valid_providers