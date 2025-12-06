from django.core.management.base import BaseCommand
from apps.campaign.models import EmissionCoefficient, TrafficClassificationRule


class Command(BaseCommand):
    help = 'Seed emission coefficients and traffic classification rules'
    
    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding emission coefficients...")
        
        coefficients = [
            # Network energy
            {
                'name': 'network_energy_per_mb',
                'component': 'network',
                'traffic_type': 'both',
                'value': 0.00015,
                'unit': 'kWh/MB',
                'description': 'Energy per MB transferred over network (SWD model)',
                'source': 'Shift Project Data Portal',
            },
            
            # Device power - Organic
            {
                'name': 'device_power',
                'component': 'device',
                'traffic_type': 'organic',
                'device_type': 'mobile',
                'value': 5.0,
                'unit': 'W',
                'description': 'Mobile device power consumption',
            },
            {
                'name': 'device_power',
                'component': 'device',
                'traffic_type': 'organic',
                'device_type': 'desktop',
                'value': 65.0,
                'unit': 'W',
                'description': 'Desktop device power consumption',
            },
            
            # Device power - Paid Ads (slightly higher due to ad rendering)
            {
                'name': 'device_power',
                'component': 'device',
                'traffic_type': 'paid_ads',
                'device_type': 'mobile',
                'value': 6.5,  # 30% higher
                'unit': 'W',
                'description': 'Mobile device power with ad rendering',
            },
            {
                'name': 'device_power',
                'component': 'device',
                'traffic_type': 'paid_ads',
                'device_type': 'desktop',
                'value': 75.0,  # 15% higher
                'unit': 'W',
                'description': 'Desktop device power with ad rendering',
            },
            
            # Ad-tech overhead (only for paid ads)
            {
                'name': 'adtech_energy_per_event',
                'component': 'adtech',
                'traffic_type': 'paid_ads',
                'platform': 'google_ads',
                'value': 1.5,
                'unit': 'Wh',
                'description': 'Energy per tracking event (Google Ads)',
            },
            {
                'name': 'adtech_energy_per_event',
                'component': 'adtech',
                'traffic_type': 'paid_ads',
                'platform': 'facebook_ads',
                'value': 1.8,
                'unit': 'Wh',
                'description': 'Energy per tracking event (Facebook Ads)',
            },
            
            # Click energy
            {
                'name': 'click_energy_per_event',
                'component': 'network',
                'traffic_type': 'both',
                'value': 0.1,
                'unit': 'Wh',
                'description': 'Energy per click event',
            },
            
            # Conversion energy
            {
                'name': 'conversion_energy_per_event',
                'component': 'server',
                'traffic_type': 'both',
                'value': 2.0,
                'unit': 'Wh',
                'description': 'Server processing energy per conversion',
            },
            
            # Default page sizes
            {
                'name': 'default_page_size_bytes',
                'component': 'network',
                'traffic_type': 'organic',
                'device_type': 'mobile',
                'value': 1.5 * 1024 * 1024,
                'unit': 'bytes',
                'description': 'Estimated mobile page size',
            },
            {
                'name': 'default_page_size_bytes',
                'component': 'network',
                'traffic_type': 'paid_ads',
                'device_type': 'mobile',
                'value': 2.0 * 1024 * 1024,  # Larger due to ad assets
                'unit': 'bytes',
                'description': 'Estimated mobile page size with ads',
            },
        ]
        
        created_count = 0
        for coef_data in coefficients:
            _, created = EmissionCoefficient.objects.get_or_create(
                name=coef_data['name'],
                component=coef_data['component'],
                traffic_type=coef_data['traffic_type'],
                device_type=coef_data.get('device_type'),
                platform=coef_data.get('platform'),
                defaults=coef_data
            )
            if created:
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} coefficients'))
        
        # Seed traffic classification rules
        rules = [
            {
                'name': 'Google Ads - CPC',
                'priority': 100,
                'conditions': {
                    'utm_source': ['google'],
                    'utm_medium': ['cpc', 'ppc'],
                },
                'traffic_type': 'paid_ads',
            },
            {
                'name': 'Facebook Ads',
                'priority': 100,
                'conditions': {
                    'utm_source': ['facebook', 'fb'],
                    'utm_medium': ['paid', 'cpc'],
                },
                'traffic_type': 'paid_ads',
            },
            {
                'name': 'Email Campaigns',
                'priority': 90,
                'conditions': {
                    'utm_medium': ['email'],
                },
                'traffic_type': 'email',
            },
            {
                'name': 'Social Media Organic',
                'priority': 50,
                'conditions': {
                    'utm_source': ['facebook', 'twitter', 'linkedin', 'instagram'],
                },
                'traffic_type': 'social',
            },
        ]
        
        rules_created = 0
        for rule_data in rules:
            _, created = TrafficClassificationRule.objects.get_or_create(
                name=rule_data['name'],
                defaults=rule_data
            )
            if created:
                rules_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {rules_created} classification rules'))