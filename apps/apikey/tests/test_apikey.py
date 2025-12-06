from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.auth.models import User
from ..models import APIKey, ConversionRule
from ..services.apikey_service import APIKeyService

User = get_user_model()


class APIKeyTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(
            email='test@example.com',
            name='Test User',
            otpverified=True,
            isactive=True
        )
        self.client.force_authenticate(user=self.user)
    
    def test_create_api_key(self):
        response = self.client.post('/api/v1/apikey/', {
            'name': 'Test API Key',
            'domain': 'example.com'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('api_key', response.json()['data'])
        self.assertIn('full_key', response.json()['data'])
    
    def test_get_api_keys(self):
        APIKeyService.create_api_key(self.user, 'Test Key', 'example.com')
        
        response = self.client.get('/api/v1/apikey/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('api_keys', response.json()['data'])
        self.assertEqual(len(response.json()['data']['api_keys']), 1)
    
    def test_delete_api_key(self):
        api_key = APIKeyService.create_api_key(self.user, 'Test Key', 'example.com')
        
        response = self.client.delete(f'/api/v1/apikey/{api_key.external_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(APIKey.objects.filter(external_id=api_key.external_id).exists())
    
    def test_toggle_api_key(self):
        api_key = APIKeyService.create_api_key(self.user, 'Test Key', 'example.com')
        
        response = self.client.patch(f'/api/v1/apikey/{api_key.external_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        api_key.refresh_from_db()
        self.assertFalse(api_key.is_active)
    
    def test_create_conversion_rule(self):
        api_key = APIKeyService.create_api_key(self.user, 'Test Key', 'example.com')
        
        response = self.client.post(f'/api/v1/apikey/{api_key.external_id}/rules/', {
            'name': 'Test Rule',
            'rule_type': 'url',
            'url_pattern': '/checkout',
            'match_type': 'contains'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ConversionRule.objects.count(), 1)
    
    def test_get_conversion_rules(self):
        api_key = APIKeyService.create_api_key(self.user, 'Test Key', 'example.com')
        ConversionRule.objects.create(
            api_key=api_key,
            name='Test Rule',
            rule_type='url',
            url_pattern='/checkout'
        )
        
        response = self.client.get(f'/api/v1/apikey/{api_key.external_id}/rules/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']['rules']), 1)