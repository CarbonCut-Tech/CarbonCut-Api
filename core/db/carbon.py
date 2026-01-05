from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from core.models.carbon_account import CarbonBalance, CarbonTransaction
import logging

logger = logging.getLogger(__name__)

class CarbonData:
    def get_balance(self, user_id: str) -> CarbonBalance:
        # why are we importing here?
        from apps.event.models import CarbonBalance as DjangoCarbonBalance
        
        orm_balance, created = DjangoCarbonBalance.objects.get_or_create(
            user_id=user_id,
            defaults={
                'total_emissions_kg': Decimal('0'),
                'balance_kg': Decimal('0'),
            }
        )
        
        return self._balance_to_domain(orm_balance)
    
    def save_balance(self, balance: CarbonBalance):
        from apps.event.models import CarbonBalance as DjangoCarbonBalance
        
        DjangoCarbonBalance.objects.update_or_create(
            user_id=balance.user_id,
            defaults={
                'total_emissions_kg': balance.total_emissions_kg,
                'balance_kg': balance.balance_kg,
                'last_transaction_at': balance.last_transaction_at,
            }
        )
    
    def save_transaction(self, transaction: CarbonTransaction):
        from apps.event.models import CarbonTransaction as DjangoCarbonTransaction
        
        DjangoCarbonTransaction.objects.create(
            user_id=transaction.user_id,
            transaction_type=transaction.transaction_type,
            amount_kg=transaction.amount_kg,
            balance_before=transaction.balance_before,
            balance_after=transaction.balance_after,
            reference_id=transaction.reference_id or '',
            reference_type=transaction.metadata.get('event_type', 'emission'),
            metadata=transaction.metadata,
        )
    
    def get_transactions(self, user_id: str, limit: int = 100) -> List[CarbonTransaction]:
        from apps.event.models import CarbonTransaction as DjangoCarbonTransaction
        
        orm_transactions = DjangoCarbonTransaction.objects.filter(
            user_id=user_id
        ).order_by('-timestamp')[:limit]
        
        return [self._transaction_to_domain(t) for t in orm_transactions]
    
    def _balance_to_domain(self, orm) -> CarbonBalance:
        return CarbonBalance(
            user_id=orm.user_id,
            total_emissions_kg=orm.total_emissions_kg,
            balance_kg=orm.balance_kg,
            last_transaction_at=orm.last_transaction_at,
        )
    
    def _transaction_to_domain(self, orm) -> CarbonTransaction:
        return CarbonTransaction(
            user_id=orm.user_id,
            transaction_type=orm.transaction_type,
            amount_kg=orm.amount_kg,
            balance_before=orm.balance_before,
            balance_after=orm.balance_after,
            timestamp=orm.timestamp,
            transaction_id=str(orm.id),  
            reference_id=orm.reference_id,
            metadata=orm.metadata,
        )