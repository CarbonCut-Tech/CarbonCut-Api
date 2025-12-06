import uuid
from django.db import models
from decimal import Decimal
from apps.auth.models import User
from apps.apikey.models import APIKey
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point


class Campaign(models.Model):
    external_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="campaigns")
    name = models.CharField(max_length=255)
    google_ads_campaign_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    google_ads_customer_id = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    total_impressions = models.BigIntegerField(default=0)
    total_clicks = models.BigIntegerField(default=0)
    total_cost_micros = models.BigIntegerField(default=0)
    total_emissions_kg = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('0.000000'))
    last_synced_at = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'campaigns'
        ordering = ['-created_at']
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
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} (User: {self.user.id})"


class UTMParameter(models.Model):
    campaign = models.ForeignKey(Campaign, related_name='utm_params', on_delete=models.CASCADE)
    key = models.CharField(max_length=50, db_index=True, default='utm_source')
    value = models.CharField(max_length=255, db_index=True)
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


class EmissionCoefficient(models.Model):
    class ComponentType(models.TextChoices):
        NETWORK = 'network', 'Network Transfer'
        DEVICE = 'device', 'Device Energy'
        ADTECH = 'adtech', 'Ad-Tech/Tracking'
        SERVER = 'server', 'Server Processing'
        CDN = 'cdn', 'CDN Distribution'
    
    class TrafficType(models.TextChoices):
        ORGANIC = 'organic', 'Organic Traffic'
        PAID_ADS = 'paid_ads', 'Paid Advertising'
        BOTH = 'both', 'Both'
    
    name = models.CharField(max_length=100, unique=True, db_index=True)
    component = models.CharField(max_length=20, choices=ComponentType.choices)
    traffic_type = models.CharField(max_length=20, choices=TrafficType.choices, default=TrafficType.BOTH)
    
    value = models.FloatField()
    unit = models.CharField(max_length=50, help_text="e.g., 'Wh/MB', 'W', 'g CO2/kWh'")
    
    device_type = models.CharField(max_length=50, blank=True, null=True)
    network_type = models.CharField(max_length=50, blank=True, null=True)
    platform = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., 'google_ads', 'facebook_ads'")
    
    description = models.TextField(blank=True)
    source = models.CharField(max_length=255, blank=True, help_text="Reference/citation for this coefficient")
    
    is_active = models.BooleanField(default=True)
    version = models.IntegerField(default=1)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'emission_coefficients'
        ordering = ['-version', 'name']
        indexes = [
            models.Index(fields=['component', 'traffic_type', 'is_active']),
            models.Index(fields=['name', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} = {self.value} {self.unit}"


class TrafficClassificationRule(models.Model):
    name = models.CharField(max_length=100)
    priority = models.IntegerField(default=0, help_text="Higher priority rules are checked first")
    
    conditions = models.JSONField(default=dict, help_text="""
    {
        "utm_source": ["google", "facebook"],
        "utm_medium": ["cpc", "paid"],
        "has_campaign_id": true,
        "referrer_domain": ["google.com", "facebook.com"]
    }
    """)
    
    traffic_type = models.CharField(max_length=20, choices=[
        ('organic', 'Organic'),
        ('paid_ads', 'Paid Ads'),
        ('social', 'Social Media'),
        ('email', 'Email'),
        ('direct', 'Direct')
    ])
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'traffic_classification_rules'
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return f"{self.name} → {self.traffic_type}"


class PointOfPresence(models.Model):
    pop_id = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, help_text="City, State/Province, Country")
    latitude = models.FloatField()
    longitude = models.FloatField()
    coordinates = gis_models.PointField(geography=True, srid=4326, null=True, blank=True)
    region = models.CharField(max_length=50, choices=[
        ('north_america', 'North America'),
        ('south_america', 'South America'),
        ('europe', 'Europe'),
        ('middle_east', 'Middle East'),
        ('asia_pacific', 'Asia Pacific'),
        ('oceania', 'Oceania'),
        ('africa', 'Africa'),
    ])

    is_active = models.BooleanField(default=True)
    capacity_gbps = models.IntegerField(default=100, help_text="Network capacity in Gbps")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'points_of_presence'
        ordering = ['region', 'name']
        indexes = [
            models.Index(fields=['region', 'is_active']),
            models.Index(fields=['pop_id']),
        ]
    
    def save(self, *args, **kwargs):
        if self.latitude and self.longitude and not self.coordinates:
            self.coordinates = Point(self.longitude, self.latitude)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.pop_id})"


class NetworkEmissionCoefficient(models.Model):
    class CoefficientType(models.TextChoices):
        NETWORK_TRANSFER = 'network_transfer', 'Network Transfer'
        CDN_DISTRIBUTION = 'cdn_distribution', 'CDN Distribution'
        AD_SERVER = 'ad_server', 'Ad Server'
        
    name = models.CharField(max_length=100, unique=True, db_index=True)
    coefficient_type = models.CharField(max_length=30, choices=CoefficientType.choices)
    
    network_type = models.CharField(max_length=50, blank=True, null=True, choices=[
        ('fiber_optic', 'Fiber Optic'),
        ('metro_fiber', 'Metro Fiber'),
        ('wireless_5g', '5G Wireless'),
        ('wireless_4g', '4G Wireless'),
        ('satellite', 'Satellite'),
        ('submarine_cable', 'Submarine Cable'),
    ])

    value = models.FloatField()
    unit = models.CharField(max_length=50, help_text="e.g., 'Wh/GB/km', 'Wh/GB'")
    
    description = models.TextField(blank=True)
    source = models.CharField(max_length=255, blank=True)
    
    is_active = models.BooleanField(default=True)
    version = models.IntegerField(default=1)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'network_emission_coefficients'
        ordering = ['-version', 'name']
        indexes = [
            models.Index(fields=['coefficient_type', 'is_active']),
            models.Index(fields=['network_type', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} = {self.value} {self.unit}"