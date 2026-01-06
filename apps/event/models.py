import uuid
from django.db import models
from django.utils import timezone
from apps.apikey.models import APIKey
from decimal import Decimal

class ActiveSession(models.Model):
    session_id = models.CharField(max_length=100, unique=True, db_index=True)
    user_id = models.CharField(max_length=255, db_index=True)
    api_key = models.CharField(max_length=255, db_index=True)
    last_event_at = models.DateTimeField(auto_now=True)
    event_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default='active', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'active_sessions'
        ordering = ['-last_event_at']
        indexes = [
            models.Index(fields=['status', 'last_event_at']),
            models.Index(fields=['user_id', 'status']),
        ]
    
    def __str__(self):
        return f"ActiveSession {self.session_id}"


class Session(models.Model):
    class SessionStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        CLOSED = 'closed', 'Closed'

    # Identity
    external_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    session_id = models.CharField(max_length=100, db_index=True)
    api_key = models.ForeignKey(APIKey, on_delete=models.CASCADE, related_name='sessions')
    user_id = models.CharField(max_length=255, db_index=True)
    
    # Timestamps
    first_event = models.DateTimeField()
    last_event = models.DateTimeField(db_index=True)
    last_processed_at = models.DateTimeField(null=True, blank=True, db_index=True)
    conversion_event = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Status & Activity
    status = models.CharField(
        max_length=20,
        choices=SessionStatus.choices,
        default=SessionStatus.ACTIVE,
        db_index=True
    )
    event_count = models.IntegerField(default=0)
    
    # Campaign & UTM
    campaign_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    utm_id = models.CharField(max_length=255, blank=True, default='')
    utm_params = models.JSONField(default=dict, blank=True)
    
    # Device & Location
    user_agent = models.TextField(blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_type = models.CharField(max_length=50, default='desktop')
    country = models.CharField(max_length=100, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')
    
    # Events summary
    events_summary = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Summary: {page_views: 10, conversions: 2}"
    )
    
    # Emissions
    total_emissions_g = models.FloatField(default=0.0, help_text="Total CO2e in grams")
    emissions_breakdown = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'sessions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session_id', 'api_key']),
            models.Index(fields=['user_id', 'status']),
            models.Index(fields=['status', 'last_event']),
            models.Index(fields=['status', 'last_processed_at']),
            models.Index(fields=['campaign_id']),
        ]
        unique_together = [['session_id', 'api_key']]

    def __str__(self):
        return f"Session {self.session_id}"


class ProcessedEvent(models.Model):
    reference_id = models.CharField(max_length=255, db_index=True)
    reference_type = models.CharField(max_length=100, db_index=True)

    user_id = models.CharField(max_length=255, db_index=True)
    session_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    
    event_type = models.CharField(max_length=100, db_index=True)
    event_data = models.JSONField(default=dict, blank=True)

    kg_co2_emitted = models.DecimalField(max_digits=20, decimal_places=6, default=Decimal('0'))

    event_timestamp = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'processed_events'
        unique_together = [['reference_id', 'reference_type']]
        indexes = [
            models.Index(fields=['user_id', 'processed_at']),
            models.Index(fields=['session_id', 'processed_at']),
            models.Index(fields=['event_type', 'processed_at']),
            models.Index(fields=['reference_type', 'processed_at']),
        ]
        ordering = ['-processed_at']
    
    def __str__(self):
        return f"{self.reference_type}:{self.reference_id}"
class CarbonBalance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user_id = models.CharField(max_length=255, unique=True, db_index=True)
    total_emissions_kg = models.DecimalField(max_digits=20, decimal_places=6, default=Decimal('0'))
    balance_kg = models.DecimalField(max_digits=20, decimal_places=6, default=Decimal('0'))
    last_transaction_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'carbon_balances'
        verbose_name = 'Carbon Balance'
        verbose_name_plural = 'Carbon Balances'
class CarbonTransaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user_id = models.CharField(max_length=255, db_index=True)

    transaction_type = models.CharField(max_length=20)
    amount_kg = models.DecimalField(max_digits=20, decimal_places=6)
    balance_before = models.DecimalField(max_digits=20, decimal_places=6)
    balance_after = models.DecimalField(max_digits=20, decimal_places=6)

    reference_id = models.CharField(max_length=255, db_index=True)
    reference_type = models.CharField(max_length=100)

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'carbon_transactions'
        indexes = [
            models.Index(fields=['user_id', 'timestamp']),
            models.Index(fields=['reference_id', 'reference_type']),
            models.Index(fields=['transaction_type', 'timestamp']),
        ]
        ordering = ['-timestamp']
        
        
class FailedEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payload = models.JSONField()
    error_message = models.TextField()
    error_traceback = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Retry'),
            ('processing', 'Processing'),
            ('resolved', 'Resolved'),
            ('abandoned', 'Abandoned'),
        ],
        default='pending',
        db_index=True
    )
    original_queue_message_id = models.CharField(max_length=255, blank=True)
    dlq_message_id = models.CharField(max_length=255, blank=True)
    failed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    last_retry_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'failed_events'
        ordering = ['-failed_at']
        indexes = [
            models.Index(fields=['status', 'retry_count']),
        ]
    
    def __str__(self):
        return f"Failed {self.event_type} - {self.status}"
class EmissionSource(models.Model):
    SCOPE_CHOICES = [
        ('scope_1', 'Scope 1 - Direct Emissions'),
        ('scope_2', 'Scope 2 - Indirect Energy'),
        ('scope_3', 'Scope 3 - Value Chain'),
    ]
    
    SOURCE_CHOICES = [
        ('cloud_aws', 'AWS Cloud'),
        ('cloud_gcp', 'GCP Cloud'),
        ('cloud_azure', 'Azure Cloud'),
        ('cdn', 'CDN Data Transfer'),
        ('website_sdk', 'Website/App SDK'),
        ('travel_flight', 'Air Travel'),
        ('travel_rail', 'Rail Travel'),
        ('travel_road', 'Road Travel'),
        ('travel_accommodation', 'Accommodation'),
        ('workforce_remote', 'Remote Work'),
        ('workforce_office', 'Office Energy'),
        ('onprem_server', 'On-Premise Servers'),
    ]
    
    ACCURACY_CHOICES = [
        ('high', 'High - Provider Data'),
        ('medium', 'Medium - Measured Data'),
        ('estimated', 'Estimated - Modeled Data'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=100, db_index=True)
    source_type = models.CharField(max_length=50, choices=SOURCE_CHOICES, db_index=True)
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, db_index=True)
    kg_co2_emitted = models.DecimalField(max_digits=15, decimal_places=6)
    emission_date = models.DateField(db_index=True)
    reference_id = models.CharField(max_length=255, db_index=True)
    metadata = models.JSONField(default=dict)
    accuracy_level = models.CharField(max_length=20, choices=ACCURACY_CHOICES, default='estimated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'emission_sources'
        indexes = [
            models.Index(fields=['user_id', 'emission_date']),
            models.Index(fields=['user_id', 'source_type', 'emission_date']),
            models.Index(fields=['user_id', 'scope']),
        ]
        ordering = ['-emission_date', '-created_at']
    
    def __str__(self):
        return f"{self.source_type} - {self.kg_co2_emitted}kg CO2e - {self.emission_date}"


class CloudProviderConnection(models.Model):
    PROVIDER_CHOICES = [
        ('aws', 'Amazon Web Services'),
        ('gcp', 'Google Cloud Platform'),
        ('azure', 'Microsoft Azure'),
    ]
    CONNECTION_TYPE_CHOICES = [
        ('csv_upload', 'CSV Upload'),
        ('api', 'API Integration'),
        ('cost_estimate', 'Cost Estimate'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=100, db_index=True)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    connection_type = models.CharField(max_length=20, choices=CONNECTION_TYPE_CHOICES)
    regions = models.JSONField(default=list)
    monthly_cost_usd = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    has_csv_data = models.BooleanField(default=False)
    last_csv_upload_date = models.DateTimeField(null=True, blank=True)
    csv_file_path = models.CharField(max_length=500, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'cloud_provider_connections'
        unique_together = ['user_id', 'provider']
        indexes = [
            models.Index(fields=['user_id', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user_id} - {self.provider}"

class CDNConnection(models.Model):
    PROVIDER_CHOICES = [
        ('cloudflare', 'Cloudflare'),
        ('aws_cloudfront', 'AWS CloudFront'),
        ('akamai', 'Akamai'),
        ('fastly', 'Fastly'),
        ('generic', 'Other/Generic CDN'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=100, db_index=True)
    provider = models.CharField(max_length=30, choices=PROVIDER_CHOICES)
    connection_type = models.CharField(max_length=20, default='manual')
    monthly_gb_transferred = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    regions = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)    
    class Meta:
        db_table = 'cdn_connections'
        indexes = [
            models.Index(fields=['user_id', 'is_active']),
        ]
class WorkforceConfiguration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=100, unique=True, db_index=True)
    total_employees = models.IntegerField(default=0)
    remote_employee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'))  # 0-100
    office_locations = models.JSONField(default=list)  
    travel_tracking_enabled = models.BooleanField(default=False)
    last_travel_upload_date = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'workforce_configurations'
class OnPremiseConfiguration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=100, db_index=True)
    server_name = models.CharField(max_length=255)
    cpu_cores = models.IntegerField()
    ram_gb = models.IntegerField()
    storage_tb = models.DecimalField(max_digits=10, decimal_places=2)
    avg_cpu_utilization = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('50'))  # 0-100
    hours_per_day = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('24'))
    days_per_month = models.IntegerField(default=30)
    location_city = models.CharField(max_length=100)
    location_country_code = models.CharField(max_length=2)
    power_usage_effectiveness = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('1.6'))
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'onpremise_configurations'
        indexes = [
            models.Index(fields=['user_id', 'is_active']),
        ]
class TravelRecord(models.Model):
    TRAVEL_TYPE_CHOICES = [
        ('flight', 'Flight'),
        ('rail', 'Rail'),
        ('road', 'Road'),
        ('accommodation', 'Accommodation'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=100, db_index=True)
    travel_type = models.CharField(max_length=20, choices=TRAVEL_TYPE_CHOICES)
    travel_date = models.DateField(db_index=True)
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    origin = models.CharField(max_length=255, null=True, blank=True)
    destination = models.CharField(max_length=255, null=True, blank=True)
    passenger_count = models.IntegerField(default=1)
    kg_co2_emitted = models.DecimalField(max_digits=15, decimal_places=6)
    metadata = models.JSONField(default=dict)  # cabin_class, vehicle_type, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'travel_records'
        indexes = [
            models.Index(fields=['user_id', 'travel_date']),
        ]
class MonthlyEmissionReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=100, db_index=True)
    year = models.IntegerField(db_index=True)
    month = models.IntegerField(db_index=True)
    total_emissions_kg = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('0'))
    scope_1_kg = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('0'))
    scope_2_kg = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('0'))
    scope_3_kg = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('0'))
    cloud_aws_kg = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('0'))
    cloud_gcp_kg = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('0'))
    cloud_azure_kg = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('0'))
    cdn_kg = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('0'))
    website_sdk_kg = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('0'))
    travel_kg = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('0'))
    workforce_kg = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('0'))
    onprem_kg = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('0'))
    source_breakdown = models.JSONField(default=dict)
    metadata = models.JSONField(default=dict)
    generated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'monthly_emission_reports'
        unique_together = ['user_id', 'year', 'month']
        indexes = [
            models.Index(fields=['user_id', 'year', 'month']),
        ]
        ordering = ['-year', '-month']
