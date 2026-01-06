import csv
from decimal import Decimal
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AWSCCFTParser:
    def parse(self, file_path: str) -> Dict[str, Any]:
        records = []
        total_emissions = Decimal('0')
        
        with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                try:
                    mbm_emissions_mt = self._clean_decimal(row.get('total_mbm_emissions_value', '0'))
                    
                    emissions_kg = mbm_emissions_mt * Decimal('1000')
                    service = self._parse_service_name(row.get('product_code', 'Other'))

                    region = self._parse_region(row.get('location', 'unknown'))
                    
                    usage_month = row.get('usage_month', '')
                    month_date = datetime.strptime(usage_month, '%Y-%m-%d')
                    
                    record = {
                        'service': service,
                        'region': region,
                        'emissions_kg': float(emissions_kg),
                        'month': month_date.strftime('%Y-%m'),
                        'emission_type': 'market_based',
                        'account_id': row.get('usage_account_id', '').strip("'"),
                        'model_version': row.get('model_version', 'unknown')
                    }
                    
                    records.append(record)
                    total_emissions += emissions_kg
                    
                    logger.info(
                        f"Parsed AWS record: {service} in {region} = {emissions_kg}kg CO2"
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to parse row: {row}. Error: {e}")
                    continue
        
        return {
            'records': records,
            'total_emissions_kg': float(total_emissions),
            'provider': 'aws',
            'record_count': len(records)
        }
    
    def _clean_decimal(self, value: str) -> Decimal:
        if not value or value.strip() == '':
            return Decimal('0')
        
        # Remove quotes and whitespace
        cleaned = value.strip().strip("'\"")
        
        try:
            return Decimal(cleaned)
        except:
            return Decimal('0')
    
    def _parse_service_name(self, product_code: str) -> str:
        service = product_code.replace('Amazon', '').replace('AWS', '').strip()

        service_map = {
            'EC2': 'EC2',
            'S3': 'S3',
            'Lambda': 'Lambda',
            'RDS': 'RDS',
            'DynamoDB': 'DynamoDB',
            'CloudFront': 'CloudFront',
            'EKS': 'EKS',
            'ECS': 'ECS',
            'Other': 'Other',
            'VPC': 'VPC',
            'ElastiCache': 'ElastiCache',
            'Redshift': 'Redshift'
        }
        
        return service_map.get(service, service)
    
    def _parse_region(self, location: str) -> str:
        region_map = {
            'Asia Pacific (Singapore)': 'ap-southeast-1',
            'Asia Pacific (Tokyo)': 'ap-northeast-1',
            'Asia Pacific (Sydney)': 'ap-southeast-2',
            'Asia Pacific (Mumbai)': 'ap-south-1',
            'US East (N. Virginia)': 'us-east-1',
            'US East (Ohio)': 'us-east-2',
            'US West (Oregon)': 'us-west-2',
            'US West (N. California)': 'us-west-1',
            'Europe (Ireland)': 'eu-west-1',
            'Europe (London)': 'eu-west-2',
            'Europe (Frankfurt)': 'eu-central-1',
            'Europe (Paris)': 'eu-west-3',
            'Canada (Central)': 'ca-central-1',
            'South America (São Paulo)': 'sa-east-1',
        }
        
        return region_map.get(location, location.lower().replace(' ', '-'))