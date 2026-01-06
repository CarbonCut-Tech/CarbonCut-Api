from decimal import Decimal
from typing import Dict, Any
from .base import BaseEmissionCalculator
from constants.emission_factors import (
    TRAVEL_FACTORS_KG_PER_KM,
    FLIGHT_RADIATIVE_FORCING
)

class TravelEmissionsCalculator(BaseEmissionCalculator):
    """
        Calculate travel emissions
        
        Input:
        - travel_type: flight, rail, road, accommodation
        - distance_km: Distance traveled (for transport)
        - nights: Number of nights (for accommodation)
        - passenger_count: Number of passengers
        - flight_class: economy, premium_economy, business, first (for flights)
        - vehicle_type: For road travel
    """
    def calculate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:

        travel_type = input_data.get('travel_type', 'flight').lower()
        
        if travel_type == 'flight':
            return self._calculate_flight(input_data)
        elif travel_type == 'rail':
            return self._calculate_rail(input_data)
        elif travel_type == 'road':
            return self._calculate_road(input_data)
        elif travel_type == 'accommodation':
            return self._calculate_accommodation(input_data)
        else:
            raise ValueError(f"Unknown travel type: {travel_type}")
    
    def _calculate_flight(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        distance_km = self._to_decimal(input_data.get('distance_km', 0))
        passenger_count = self._to_decimal(input_data.get('passenger_count', 1))
        flight_class = input_data.get('flight_class', 'economy').lower()
        is_domestic = input_data.get('is_domestic', False)

        if is_domestic:
            factor_key = 'flight_domestic'
        else:
            if flight_class == 'economy':
                factor_key = 'flight_intl_economy'
            elif flight_class == 'premium_economy':
                factor_key = 'flight_intl_premium_economy'
            elif flight_class == 'business':
                factor_key = 'flight_intl_business'
            elif flight_class == 'first':
                factor_key = 'flight_intl_first'
            else:
                factor_key = 'flight_intl_economy'
        
        emission_factor = TRAVEL_FACTORS_KG_PER_KM[factor_key]

        base_emissions_kg = distance_km * emission_factor * passenger_count
        total_emissions_kg = base_emissions_kg * FLIGHT_RADIATIVE_FORCING
        
        return {
            'total_emissions_kg': float(total_emissions_kg),
            'total_emissions_g': float(total_emissions_kg * 1000),
            'breakdown': {
                'distance_km': float(distance_km),
                'passenger_count': int(passenger_count),
                'base_emissions_kg': float(base_emissions_kg),
                'radiative_forcing_multiplier': float(FLIGHT_RADIATIVE_FORCING),
                'emissions_with_rf_kg': float(total_emissions_kg)
            },
            'factors': {
                'travel_type': 'flight',
                'flight_class': flight_class,
                'is_domestic': is_domestic,
                'emission_factor_kg_per_km': float(emission_factor),
                'source': 'DEFRA 2024',
                'version': self.VERSION
            }
        }
    
    def _calculate_rail(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        distance_km = self._to_decimal(input_data.get('distance_km', 0))
        passenger_count = self._to_decimal(input_data.get('passenger_count', 1))
        rail_type = input_data.get('rail_type', 'national').lower()
        
        if rail_type == 'international':
            factor_key = 'rail_international'
        else:
            factor_key = 'rail_national'
        
        emission_factor = TRAVEL_FACTORS_KG_PER_KM[factor_key]
        total_emissions_kg = distance_km * emission_factor * passenger_count
        
        return {
            'total_emissions_kg': float(total_emissions_kg),
            'total_emissions_g': float(total_emissions_kg * 1000),
            'breakdown': {
                'distance_km': float(distance_km),
                'passenger_count': int(passenger_count)
            },
            'factors': {
                'travel_type': 'rail',
                'rail_type': rail_type,
                'emission_factor_kg_per_km': float(emission_factor),
                'source': 'DEFRA 2024',
                'version': self.VERSION
            }
        }
    
    def _calculate_road(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        distance_km = self._to_decimal(input_data.get('distance_km', 0))
        vehicle_type = input_data.get('vehicle_type', 'car_petrol_medium').lower()
        
        # Default to medium petrol car if not found
        emission_factor = TRAVEL_FACTORS_KG_PER_KM.get(
            vehicle_type,
            TRAVEL_FACTORS_KG_PER_KM['car_petrol_medium']
        )
        
        total_emissions_kg = distance_km * emission_factor
        
        return {
            'total_emissions_kg': float(total_emissions_kg),
            'total_emissions_g': float(total_emissions_kg * 1000),
            'breakdown': {
                'distance_km': float(distance_km),
                'vehicle_type': vehicle_type
            },
            'factors': {
                'travel_type': 'road',
                'emission_factor_kg_per_km': float(emission_factor),
                'source': 'DEFRA 2024',
                'version': self.VERSION
            }
        }
    
    def _calculate_accommodation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        nights = self._to_decimal(input_data.get('nights', 0))
        country_code = input_data.get('country_code', 'WORLD').upper()
        if country_code == 'GB':
            emission_factor = TRAVEL_FACTORS_KG_PER_KM['hotel_night_uk']
        else:
            emission_factor = TRAVEL_FACTORS_KG_PER_KM['hotel_night_average']
        
        total_emissions_kg = nights * emission_factor
        
        return {
            'total_emissions_kg': float(total_emissions_kg),
            'total_emissions_g': float(total_emissions_kg * 1000),
            'breakdown': {
                'nights': int(nights),
                'country_code': country_code
            },
            'factors': {
                'travel_type': 'accommodation',
                'emission_factor_kg_per_night': float(emission_factor),
                'source': 'DEFRA 2024',
                'version': self.VERSION
            }
        }