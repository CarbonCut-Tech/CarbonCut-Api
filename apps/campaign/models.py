import uuid
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.auth.models import User, ProviderType
class Campaign(models.Model):
    external_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="campaigns")
    name = models.CharField(max_length=255)
    
    google_ads_campaign_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    google_ads_customer_id = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    
    total_impressions = models.BigIntegerField(default=0)
    total_clicks = models.BigIntegerField(default=0)
    total_cost_micros = models.BigIntegerField(default=0)

    total_emissions_kg = models.DecimalField(
        max_digits=15, 
        decimal_places=6, 
        default=Decimal('0.000000')
    )

    last_synced_at = models.DateTimeField(null=True, blank=True)

    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'campaigns'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'google_ads_campaign_id', 'google_ads_customer_id'],
                name='unique_user_google_campaign',
                condition=models.Q(google_ads_campaign_id__isnull=False) & 
                          models.Q(google_ads_customer_id__isnull=False)
            )
        ]
        indexes = [
            models.Index(fields=['user', 'google_ads_customer_id']),
            models.Index(fields=['google_ads_campaign_id']),
            models.Index(fields=['is_archived']),
            models.Index(fields=['-created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} (User: {self.user.email})"


class UTMParameter(models.Model):
    campaign = models.ForeignKey(Campaign, related_name='utm_params', on_delete=models.CASCADE)
    key = models.CharField(max_length=50, db_index=True, default='utm_source')
    value = models.CharField(max_length=255, db_index=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="utm_parameters")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'utm_parameters'
        unique_together = [['campaign', 'key']]
        indexes = [
            models.Index(fields=['campaign', 'key']),
            models.Index(fields=['value']),
        ]

    def __str__(self):
        return f"{self.key}={self.value}"


class CampaignEmission(models.Model):
    external_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='emissions')
    
    date = models.DateField(db_index=True)
    hour = models.IntegerField(null=True, blank=True)
    
    country = models.CharField(max_length=100, db_index=True, default='United States')
    region = models.CharField(max_length=100, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    
    device_type = models.CharField(max_length=50, default='desktop', db_index=True)
    page_views = models.IntegerField(default=0)
    clicks = models.IntegerField(default=0)
    conversions = models.IntegerField(default=0)
    sessions = models.IntegerField(default=0)
    
    impressions = models.BigIntegerField(default=0)
    ad_clicks = models.BigIntegerField(default=0)
    cost_micros = models.BigIntegerField(default=0)
    
    impression_emissions_g = models.DecimalField(
        max_digits=15, 
        decimal_places=6, 
        default=Decimal('0.000000')
    )
    page_view_emissions_g = models.DecimalField(
        max_digits=15, 
        decimal_places=6, 
        default=Decimal('0.000000')
    )
    click_emissions_g = models.DecimalField(
        max_digits=15, 
        decimal_places=6, 
        default=Decimal('0.000000')
    )
    conversion_emissions_g = models.DecimalField(
        max_digits=15, 
        decimal_places=6, 
        default=Decimal('0.000000')
    )
    total_emissions_g = models.DecimalField(
        max_digits=15, 
        decimal_places=6, 
        default=Decimal('0.000000')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'campaign_emissions'
        unique_together = [['campaign', 'date', 'hour', 'country', 'region', 'device_type']]
        indexes = [
            models.Index(fields=['campaign', 'date']),
            models.Index(fields=['country', 'date']),
            models.Index(fields=['device_type', 'date']),
            models.Index(fields=['date', 'hour']),
            models.Index(fields=['-date']),
        ]
        ordering = ['-date', '-hour']
    
    def __str__(self):
        return f"{self.campaign.name} - {self.date} ({self.country})"