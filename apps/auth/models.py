import uuid
from django.db import models

class ProviderType(models.TextChoices):
    LINKEDIN = "linkedin", "LinkedIn"
    GOOGLE_ADS = "google_ads", "Google Ads"
    META_ADS = "meta_ads", "Meta Ads"


class BaseEntity(models.Model):
    external_id = models.CharField(
        max_length=64, unique=True, default=uuid.uuid4, editable=False
    )

    extras = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        
class User(models.Model):
    id = models.TextField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    name = models.TextField(blank=True, null=True)
    phonenumber = models.TextField(db_column='phoneNumber', blank=True, null=True)
    companyname = models.TextField(db_column='companyName', blank=True, null=True)
    createdat = models.DateTimeField(db_column='createdAt', auto_now_add=True)
    updatedat = models.DateTimeField(db_column='updatedAt', auto_now=True)
    otpcode = models.TextField(db_column='otpCode', blank=True, null=True)
    otpexpiry = models.DateTimeField(db_column='otpExpiry', blank=True, null=True)
    otpverified = models.BooleanField(db_column='otpVerified', default=False)
    isactive = models.BooleanField(db_column='isActive', default=True)
    onboarded = models.BooleanField(db_column='onboarded', default=False)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        managed = True
        db_table = 'user'

class Credential(models.Model):
    id = models.TextField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.CharField(max_length=32, choices=ProviderType.choices)  # <-- enum here
    provider_user_id = models.TextField()
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'credential'
        unique_together = (('provider', 'provider_user_id'),)