import uuid
from django.db import models
from apps.apikey.models import APIKey


class Session(models.Model):
    class SessionStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        PROCESSING = 'processing', 'Processing'
        CLOSED = 'closed', 'Closed'

    external_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    session_id = models.CharField(max_length=100, db_index=True)
    campaign_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    utm_id = models.CharField(max_length=255, blank=True, default='')

    api_key = models.ForeignKey(APIKey, on_delete=models.CASCADE, related_name='sessions')
    
    first_event = models.DateTimeField()
    last_event = models.DateTimeField()
    conversion_event = models.DateTimeField(null=True, blank=True)
    last_processed_at = models.DateTimeField(null=True, blank=True)
    
    events = models.JSONField(default=list, blank=True)
    
    user_agent = models.TextField(blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_type = models.CharField(max_length=50, default='desktop')
    

    country = models.CharField(max_length=100, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    location_accuracy = models.FloatField(null=True, blank=True)
    location_source = models.CharField(max_length=50, default='ip_geolocation')
    

    status = models.CharField(
        max_length=20,
        choices=SessionStatus.choices,
        default=SessionStatus.ACTIVE,
        db_index=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_emissions_g = models.FloatField(default=0.0, help_text="Total CO2e in grams")
    emissions_breakdown = models.JSONField(default=dict, blank=True, help_text="Detailed emission breakdown")

    class Meta:
        db_table = 'sessions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session_id', 'api_key']),
            models.Index(fields=['campaign_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['utm_id']),
            models.Index(fields=['status', 'last_event']),
        ]
        unique_together = [['session_id', 'api_key']]

    def __str__(self):
        return f"Session {self.session_id}"