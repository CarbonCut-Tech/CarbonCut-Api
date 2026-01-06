# Create: core/services/emission_reporting.py

from typing import Dict, Any, List, Optional
from datetime import date, datetime
from decimal import Decimal
from core.db.emission_sources import EmissionSourceData
from core.db.users import UserData
import logging
from calendar import monthrange

logger = logging.getLogger(__name__)


class EmissionReportingService:
    def __init__(self):
        self.emission_data = EmissionSourceData()
        self.user_data = UserData()
    
    def generate_monthly_report(
        self,
        user_id: str,
        month: int,
        year: int
    ) -> Dict[str, Any]:
        logger.info(f"Generating monthly report for user {user_id}: {year}-{month:02d}")
        
        # Get monthly summary from database
        summary = self.emission_data.get_monthly_summary(user_id, month, year)
        
        if summary['total_kg'] == 0:
            return self._empty_report(user_id, month, year)
        
        # Calculate scope breakdown with percentages
        scope_breakdown = self._calculate_scope_breakdown(summary['by_scope'], summary['total_kg'])
        
        # Calculate source breakdown with metadata
        source_breakdown = self._calculate_source_breakdown(summary['by_source'], summary['total_kg'])
        
        # Get trends (compare with previous months)
        trends = self._calculate_trends(user_id, month, year)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            summary['total_kg'],
            scope_breakdown,
            source_breakdown
        )
        
        return {
            'user_id': user_id,
            'period': f"{year}-{month:02d}",
            'month': month,
            'year': year,
            'total_emissions_kg': float(summary['total_kg']),
            'total_emissions_tonnes': float(summary['total_kg'] / 1000),
            'scope_breakdown': scope_breakdown,
            'source_breakdown': source_breakdown,
            'trends': trends,
            'recommendations': recommendations,
            'generated_at': datetime.now().isoformat()
        }
    
    def get_scope_breakdown(
        self,
        user_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        emissions = self.emission_data.get_by_date_range(user_id, start_date, end_date)
        
        scope_totals = {
            'scope_1': Decimal('0'),
            'scope_2': Decimal('0'),
            'scope_3': Decimal('0')
        }
        
        for emission in emissions:
            scope = emission['scope']
            scope_totals[scope] += Decimal(str(emission['kg_co2_emitted']))
        
        total = sum(scope_totals.values())
        
        return {
            'total_kg': float(total),
            'scope_1': {
                'kg_co2': float(scope_totals['scope_1']),
                'percentage': float((scope_totals['scope_1'] / total * 100) if total > 0 else 0),
                'description': 'Direct emissions from owned/controlled sources'
            },
            'scope_2': {
                'kg_co2': float(scope_totals['scope_2']),
                'percentage': float((scope_totals['scope_2'] / total * 100) if total > 0 else 0),
                'description': 'Indirect emissions from purchased energy'
            },
            'scope_3': {
                'kg_co2': float(scope_totals['scope_3']),
                'percentage': float((scope_totals['scope_3'] / total * 100) if total > 0 else 0),
                'description': 'All other indirect emissions in value chain'
            }
        }
    
    def get_emissions_by_source(
        self,
        user_id: str,
        month: int,
        year: int
    ) -> Dict[str, Any]:
        """Get emissions grouped by source type"""
        
        summary = self.emission_data.get_monthly_summary(user_id, month, year)
        
        return {
            'user_id': user_id,
            'period': f"{year}-{month:02d}",
            'sources': {k: float(v) for k, v in summary['by_source'].items()},
            'total_kg': float(summary['total_kg'])
        }
    
    def export_csrd_compliant(
        self,
        user_id: str,
        year: int
    ) -> Dict[str, Any]:
        logger.info(f"Generating CSRD-compliant report for user {user_id}, year {year}")
        
        annual_total = Decimal('0')
        monthly_data = []
        scope_annual = {'scope_1': Decimal('0'), 'scope_2': Decimal('0'), 'scope_3': Decimal('0')}
        
        for month in range(1, 13):
            summary = self.emission_data.get_monthly_summary(user_id, month, year)
            annual_total += summary['total_kg']
            
            for scope, value in summary['by_scope'].items():
                scope_annual[scope] += value
            
            monthly_data.append({
                'month': month,
                'total_kg': float(summary['total_kg']),
                'by_scope': {k: float(v) for k, v in summary['by_scope'].items()}
            })
        
        user = self.user_data.get_by_id(user_id)
        
        return {
            'reporting_standard': 'ESRS E1 - Climate Change',
            'reporting_period': {
                'year': year,
                'start_date': f"{year}-01-01",
                'end_date': f"{year}-12-31"
            },
            'organization': {
                'user_id': user_id,
                'company_name': user.company_name if user else None,
                'email': user.email if user else None
            },
            'greenhouse_gas_emissions': {
                'total_emissions_tco2e': float(annual_total / 1000),
                'total_emissions_kgco2e': float(annual_total),
                'scope_1_tco2e': float(scope_annual['scope_1'] / 1000),
                'scope_2_tco2e': float(scope_annual['scope_2'] / 1000),
                'scope_3_tco2e': float(scope_annual['scope_3'] / 1000),
                'scope_breakdown_percentage': {
                    'scope_1': float((scope_annual['scope_1'] / annual_total * 100) if annual_total > 0 else 0),
                    'scope_2': float((scope_annual['scope_2'] / annual_total * 100) if annual_total > 0 else 0),
                    'scope_3': float((scope_annual['scope_3'] / annual_total * 100) if annual_total > 0 else 0)
                }
            },
            'monthly_breakdown': monthly_data,
            'methodology': {
                'calculation_standards': [
                    'GHG Protocol Corporate Standard',
                    'ISO 14064-1:2018',
                    'DEFRA 2024 Emission Factors'
                ],
                'data_quality': 'Mix of measured data and industry-standard estimates',
                'boundaries': 'Organizational boundary - operational control approach'
            },
            'generated_at': datetime.now().isoformat(),
            'version': '1.0'
        }
    
    def _calculate_scope_breakdown(
        self,
        by_scope: Dict[str, Decimal],
        total: Decimal
    ) -> Dict[str, Dict[str, float]]:
        breakdown = {}
        for scope, value in by_scope.items():
            percentage = (value / total * 100) if total > 0 else 0
            breakdown[scope] = {
                'kg_co2': float(value),
                'percentage': float(percentage)
            }
        
        return breakdown
    
    def _calculate_source_breakdown(
        self,
        by_source: Dict[str, Decimal],
        total: Decimal
    ) -> Dict[str, Dict[str, Any]]:
        source_scope_map = {
            'cloud_aws': 'scope_2',
            'cloud_gcp': 'scope_2',
            'cloud_azure': 'scope_2',
            'cdn': 'scope_3',
            'website_sdk': 'scope_3',
            'travel_flight': 'scope_3',
            'travel_rail': 'scope_3',
            'travel_road': 'scope_3',
            'travel_accommodation': 'scope_3',
            'workforce_remote': 'scope_3',
            'workforce_office': 'scope_2',
            'onprem_server': 'scope_1'
        }
        
        source_accuracy_map = {
            'cloud_aws': 'high',
            'cloud_gcp': 'high',
            'cloud_azure': 'high',
            'cdn': 'medium',
            'website_sdk': 'medium',
            'travel_flight': 'high',
            'travel_rail': 'high',
            'travel_road': 'medium',
            'travel_accommodation': 'medium',
            'workforce_remote': 'estimated',
            'workforce_office': 'medium',
            'onprem_server': 'estimated'
        }
        
        breakdown = {}
        for source, value in by_source.items():
            breakdown[source] = {
                'kg_co2': float(value),
                'percentage': float((value / total * 100) if total > 0 else 0),
                'scope': source_scope_map.get(source, 'scope_3'),
                'accuracy': source_accuracy_map.get(source, 'estimated')
            }
        
        return breakdown
    
    def _calculate_trends(
        self,
        user_id: str,
        current_month: int,
        current_year: int
    ) -> Dict[str, Any]:
        current = self.emission_data.get_monthly_summary(user_id, current_month, current_year)

        prev_month = current_month - 1 if current_month > 1 else 12
        prev_year = current_year if current_month > 1 else current_year - 1
        previous = self.emission_data.get_monthly_summary(user_id, prev_month, prev_year)

        current_total = current['total_kg']
        previous_total = previous['total_kg']
        
        if previous_total > 0:
            change_kg = current_total - previous_total
            change_percentage = (change_kg / previous_total) * 100
        else:
            change_kg = current_total
            change_percentage = 100 if current_total > 0 else 0
        
        return {
            'current_month': {
                'month': current_month,
                'year': current_year,
                'total_kg': float(current_total)
            },
            'previous_month': {
                'month': prev_month,
                'year': prev_year,
                'total_kg': float(previous_total)
            },
            'change': {
                'kg_co2': float(change_kg),
                'percentage': float(change_percentage),
                'direction': 'increase' if change_kg > 0 else 'decrease' if change_kg < 0 else 'stable'
            }
        }
    
    # def _generate_recommendations(
    #     self,
    #     total_kg: Decimal,
    #     scope_breakdown: Dict[str, Dict[str, float]],
    #     source_breakdown: Dict[str, Dict[str, Any]]
    # ) -> List[str]:
    #     recommendations = []
        
    #     if scope_breakdown.get('scope_3', {}).get('percentage', 0) > 60:
    #         recommendations.append(
    #             "Scope 3 emissions are your largest contributor. "
    #             "Focus on supply chain engagement and remote work policies."
    #         )
        
    #     # Cloud emissions high
    #     cloud_sources = ['cloud_aws', 'cloud_gcp', 'cloud_azure']
    #     cloud_total = sum(
    #         source_breakdown.get(src, {}).get('kg_co2', 0)
    #         for src in cloud_sources
    #     )
    #     if cloud_total > float(total_kg) * 0.5:
    #         recommendations.append(
    #             "Cloud infrastructure is your primary emission source. "
    #             "Consider migrating to low-carbon regions and optimizing resource usage."
    #         )
        
    #     # Travel emissions present
    #     travel_sources = ['travel_flight', 'travel_rail', 'travel_road']
    #     travel_total = sum(
    #         source_breakdown.get(src, {}).get('kg_co2', 0)
    #         for src in travel_sources
    #     )
    #     if travel_total > 0:
    #         recommendations.append(
    #             f"Travel emissions: {travel_total:.2f}kg CO2. "
    #             "Consider virtual meetings and rail over air travel where possible."
    #         )
        
    #     # Website tracking
    #     website_total = source_breakdown.get('website_sdk', {}).get('kg_co2', 0)
    #     if website_total > 0:
    #         recommendations.append(
    #             "Optimize website performance: reduce page weight, "
    #             "compress images, and implement lazy loading to reduce digital emissions."
    #         )
        
    #     # Generic recommendation
    #     if not recommendations:
    #         recommendations.append(
    #             "Continue monitoring your emissions. "
    #             "Upload cloud provider CSV data for more accurate reporting."
    #         )
        
    #     return recommendations
    
    # def _empty_report(
    #     self,
    #     user_id: str,
    #     month: int,
    #     year: int
    # ) -> Dict[str, Any]:
    #     """Return empty report structure"""
        
    #     return {
    #         'user_id': user_id,
    #         'period': f"{year}-{month:02d}",
    #         'month': month,
    #         'year': year,
    #         'total_emissions_kg': 0,
    #         'total_emissions_tonnes': 0,
    #         'scope_breakdown': {},
    #         'source_breakdown': {},
    #         'trends': None,
    #         'recommendations': [
    #             "No emissions recorded for this period. "
    #             "Configure your emission sources to start tracking."
    #         ],
    #         'generated_at': datetime.now().isoformat()
    #     }