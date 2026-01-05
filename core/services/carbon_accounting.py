from decimal import Decimal
from datetime import datetime
from typing import Optional
from django.utils import timezone
from ..models.carbon_account import CarbonBalance, CarbonTransaction
import logging

logger = logging.getLogger(__name__)

class CarbonAccountingService:
    def record_emission(
        self,
        balance: CarbonBalance,
        amount_kg: Decimal,
        reference_id: Optional[str] = None,
        metadata: dict = None
    ) -> CarbonTransaction:
    
        logger.info(f"Recording emission: {amount_kg}kg CO2e")
        
        balance_before = balance.balance_kg
        balance.add_emission(amount_kg)
        
        transaction = CarbonTransaction(
            user_id=balance.user_id,
            transaction_type='emission',
            amount_kg=amount_kg,
            balance_before=balance_before,
            balance_after=balance.balance_kg,
            timestamp=timezone.now(),  # Use timezone-aware datetime
            reference_id=reference_id,
            metadata=metadata or {}
        )
        
        return transaction
    
    def record_offset(
        self,
        balance: CarbonBalance,
        amount_kg: Decimal,
        price_per_kg: Decimal,
        provider: str,
        certificate_id: str,
        metadata: dict = None
    ) -> tuple[CarbonTransaction, dict]:
        
        if amount_kg <= 0:
            raise ValueError("Offset amount must be positive")
        
        if amount_kg > balance.balance_kg:
            raise ValueError(
                f"Cannot offset {amount_kg}kg - current balance is {balance.balance_kg}kg"
            )
        
        balance_before = balance.balance_kg
        balance.subtract_offset(amount_kg)
        
        total_cost = amount_kg * price_per_kg
        
        transaction = CarbonTransaction(
            user_id=balance.user_id,
            transaction_type='offset',
            amount_kg=-amount_kg,
            balance_before=balance_before,
            balance_after=balance.balance_kg,
            timestamp=timezone.now(),  # Use timezone-aware datetime
            metadata={
                'provider': provider,
                'certificate_id': certificate_id,
                'price_per_kg': float(price_per_kg),
                'total_cost': float(total_cost),
                **(metadata or {})
            }
        )
        
        offset_details = {
            'amount_kg': amount_kg,
            'price_per_kg': price_per_kg,
            'total_cost': total_cost,
            'provider': provider,
            'certificate_id': certificate_id
        }
        
        return transaction, offset_details
    
    def get_summary(self, balance: CarbonBalance) -> dict:
        return {
            'user_id': balance.user_id,
            'total_emissions_kg': float(balance.total_emissions_kg),
            'balance_kg': float(balance.balance_kg),
            'is_carbon_neutral': balance.is_carbon_neutral(),
            'last_transaction_at': balance.last_transaction_at
        }