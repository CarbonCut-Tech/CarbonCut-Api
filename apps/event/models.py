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

# this should be in common codebasee
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

# this should be in common codebasee
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
