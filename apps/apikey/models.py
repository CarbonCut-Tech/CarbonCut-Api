import uuid
from django.db import models
from django.utils import timezone


class APIKey(models.Model):
    external_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    key = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    user_id = models.CharField(max_length=100, db_index=True)
    is_active = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)
    domain = models.CharField(max_length=255, default='*')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'api_keys'
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['key']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.key[:10]}...)"


class ConversionRuleType(models.TextChoices):
    URL = 'url', 'URL Match'
    CLICK = 'click', 'Element Click'
    FORM_SUBMIT = 'form_submit', 'Form Submission'
    CUSTOM_EVENT = 'custom_event', 'Custom Event'


class ConversionMatchType(models.TextChoices):
    EXACT = 'exact', 'Exact Match'
    CONTAINS = 'contains', 'Contains'
    STARTS_WITH = 'starts_with', 'Starts With'
    ENDS_WITH = 'ends_with', 'Ends With'
    REGEX = 'regex', 'Regular Expression'
    QUERY_PARAM = 'query_param', 'Query Parameter'


class ConversionRule(models.Model):
    external_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    api_key = models.ForeignKey(APIKey, on_delete=models.CASCADE, related_name='conversion_rules')
    rule_type = models.CharField(max_length=50, choices=ConversionRuleType.choices, default=ConversionRuleType.URL)
    name = models.CharField(max_length=255)
    url_pattern = models.CharField(max_length=500, blank=True, null=True)
    match_type = models.CharField(max_length=50, choices=ConversionMatchType.choices, default=ConversionMatchType.CONTAINS)
    css_selector = models.CharField(max_length=500, blank=True, null=True)
    element_text = models.CharField(max_length=255, blank=True, null=True)
    form_id = models.CharField(max_length=255, blank=True, null=True)
    custom_event_name = models.CharField(max_length=255, blank=True, null=True)
    track_value = models.BooleanField(default=False)
    value_selector = models.CharField(max_length=500, blank=True, null=True)
    default_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    conversion_count = models.IntegerField(default=0)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'conversion_rules'
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['api_key', 'is_active']),
            models.Index(fields=['rule_type']),
            models.Index(fields=['priority']),
        ]

    def __str__(self):
        return f"{self.name} ({self.rule_type}) - {self.api_key.name}"

    def increment_conversion_count(self):
        self.conversion_count += 1
        self.last_triggered_at = timezone.now()
        self.save(update_fields=['conversion_count', 'last_triggered_at'])
