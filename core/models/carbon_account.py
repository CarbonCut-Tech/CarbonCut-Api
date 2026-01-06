from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional
from django.utils import timezone

@dataclass
class CarbonBalance:
    user_id: str
    total_emissions_kg: Decimal = Decimal('0')
    balance_kg: Decimal = Decimal('0')
    last_transaction_at: Optional[datetime] = None
    
    def add_emission(self, amount_kg: Decimal):
        self.total_emissions_kg += amount_kg
        self.balance_kg += amount_kg
        self.last_transaction_at = timezone.now()  
    
    def subtract_offset(self, amount_kg: Decimal):
        self.balance_kg -= amount_kg
        self.last_transaction_at = timezone.now()  
    
    def is_carbon_neutral(self) -> bool:
        return self.balance_kg <= Decimal('0')

@dataclass
class CarbonTransaction:
    user_id: str
    transaction_type: str
    amount_kg: Decimal
    balance_before: Decimal
    balance_after: Decimal
    timestamp: datetime
    transaction_id: Optional[str] = None
    reference_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)

@dataclass
class CarbonOffset:
    user_id: str
    amount_kg: Decimal
    price_per_kg: Decimal
    provider: str
    certificate_id: str
    status: str = 'completed'
    purchased_at: datetime = field(default_factory=timezone.now) 
    metadata: dict = field(default_factory=dict)
    
    @property
    def total_cost(self) -> Decimal:
        return self.amount_kg * self.price_per_kg