from typing import Dict, Type
from .base import BaseEmissionCalculator
from .internet_ads import InternetAdsCalculator
from .internet_website import InternetWebsiteCalculator
from .oil_gas_lubricant import OilGasLubricantCalculator
from .cloud_emissions import CloudEmissionsCalculator
from .cdn_data_transfer import CDNDataTransferCalculator
from .travel_emissions import TravelEmissionsCalculator
from .workforce_emissions import WorkforceEmissionsCalculator
from .onprem_servers import OnPremServerCalculator


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
    
    @classmethod
    def get_by_source_type(cls, source_type: str) -> BaseEmissionCalculator:
        source_to_calculator = {
            'cloud_aws': 'cloud:aws',
            'cloud_gcp': 'cloud:gcp',
            'cloud_azure': 'cloud:azure',
            'cdn': 'cdn:transfer',
            'travel_flight': 'travel:flight',
            'travel_rail': 'travel:rail',
            'travel_road': 'travel:road',
            'travel_accommodation': 'travel:accommodation',
            'workforce_remote': 'workforce:remote',
            'workforce_office': 'workforce:office',
            'onprem_server': 'onprem:server',
            'website_sdk': 'internet:website',
        }
        
        key = source_to_calculator.get(source_type)
        if not key:
            raise ValueError(f"No calculator for source type: {source_type}")
        
        calculator_class = cls._calculators.get(key)
        if not calculator_class:
            raise ValueError(f"Calculator not registered: {key}")
        
        return calculator_class()


CalculatorRegistry.register('internet', 'ads', InternetAdsCalculator)
CalculatorRegistry.register('internet', 'website', InternetWebsiteCalculator)
CalculatorRegistry.register('oil-and-gas', 'lubricant', OilGasLubricantCalculator)

CalculatorRegistry.register('cloud', 'aws', CloudEmissionsCalculator)
CalculatorRegistry.register('cloud', 'gcp', CloudEmissionsCalculator)
CalculatorRegistry.register('cloud', 'azure', CloudEmissionsCalculator)
CalculatorRegistry.register('cdn', 'transfer', CDNDataTransferCalculator)
CalculatorRegistry.register('travel', 'flight', TravelEmissionsCalculator)
CalculatorRegistry.register('travel', 'rail', TravelEmissionsCalculator)
CalculatorRegistry.register('travel', 'road', TravelEmissionsCalculator)
CalculatorRegistry.register('travel', 'accommodation', TravelEmissionsCalculator)
CalculatorRegistry.register('workforce', 'remote', WorkforceEmissionsCalculator)
CalculatorRegistry.register('workforce', 'office', WorkforceEmissionsCalculator)
CalculatorRegistry.register('onprem', 'server', OnPremServerCalculator)