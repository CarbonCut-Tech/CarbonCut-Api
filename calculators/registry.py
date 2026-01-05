from typing import Dict, Type
from .base import BaseEmissionCalculator
from .internet_ads import InternetAdsCalculator
from .internet_website import InternetWebsiteCalculator
from .oil_gas_lubricant import OilGasLubricantCalculator


class CalculatorRegistry:
    _calculators: Dict[str, Type[BaseEmissionCalculator]] = {}
    
    @classmethod
    def register(cls, category_slug: str, industry_slug: str, calculator: Type[BaseEmissionCalculator]):
        key = f"{category_slug}:{industry_slug}"
        cls._calculators[key] = calculator
    
    @classmethod
    def get_calculator(cls, category_slug: str, industry_slug: str) -> BaseEmissionCalculator:
        key = f"{category_slug}:{industry_slug}"
        calculator_class = cls._calculators.get(key)
        if not calculator_class:
            raise ValueError(f"No calculator registered for {key}")
        return calculator_class()
    
    @classmethod
    def is_registered(cls, category_slug: str, industry_slug: str) -> bool:
        key = f"{category_slug}:{industry_slug}"
        return key in cls._calculators


CalculatorRegistry.register('internet', 'ads', InternetAdsCalculator)
CalculatorRegistry.register('internet', 'website', InternetWebsiteCalculator)
CalculatorRegistry.register('oil-and-gas', 'lubricant', OilGasLubricantCalculator)