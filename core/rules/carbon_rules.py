from decimal import Decimal

class CarbonRules:
    
    MIN_OFFSET_AMOUNT = Decimal('0.001')
    MAX_OFFSET_AMOUNT = Decimal('10000')
    DEFAULT_OFFSET_PRICE = Decimal('15.00')
    
    def validate_emission_amount(self, amount_kg: Decimal) -> bool:
        return amount_kg > 0 and amount_kg < Decimal('1000')
    
    def validate_offset_amount(self, amount_kg: Decimal) -> bool:
        return (
            amount_kg >= self.MIN_OFFSET_AMOUNT and 
            amount_kg <= self.MAX_OFFSET_AMOUNT
        )
    
    def calculate_offset_cost(
        self, 
        amount_kg: Decimal, 
        price_per_kg: Decimal = None
    ) -> Decimal:
        price = price_per_kg or self.DEFAULT_OFFSET_PRICE
        return amount_kg * price