import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class ProviderType(models.TextChoices):
    LINKEDIN = "linkedin", "LinkedIn"
    GOOGLE_ADS = "google_ads", "Google Ads"
    META_ADS = "meta_ads", "Meta Ads"
    DV360 = "dv360", "Display & Video 360"
    TIKTOK = "tiktok", "TikTok"
    SNAPCHAT = "snapchat", "Snapchat"
    TWITTER_X = "twitter_x", "Twitter/X"

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('isactive', True)
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser):
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
    onboarded = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        managed = True
        db_table = 'users'

    def __str__(self):
        return self.email
    
    def has_perm(self, perm, obj=None):
        return self.is_superuser
    
    def has_module_perms(self, app_label):
        return self.is_superuser


class Credential(models.Model):
    id = models.TextField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='credentials'
    )
    provider = models.CharField(
        max_length=32, 
        choices=ProviderType.choices,
        help_text="OAuth provider (Google Ads, Meta, LinkedIn, etc.)"
    )
    provider_user_id = models.TextField(
        help_text="User ID from the provider's system"
    )
    access_token = models.TextField(
        help_text="OAuth access token for API calls"
    )
    refresh_token = models.TextField(
        blank=True, 
        null=True,
        help_text="OAuth refresh token for renewing access"
    )
    expires_at = models.DateTimeField(
        blank=True, 
        null=True,
        help_text="Token expiration timestamp"
    )
    scopes = models.TextField(
        blank=True,
        null=True,
        help_text="Comma-separated list of granted scopes"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    extras = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Additional provider-specific metadata"
    )

    class Meta:
        managed = True
        db_table = 'credentials'
        unique_together = (('user', 'provider', 'provider_user_id'),)
        indexes = [
            models.Index(fields=['user', 'provider']),
            models.Index(fields=['provider', 'provider_user_id']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.get_provider_display()}"
    
    def is_expired(self):
        if not self.expires_at:
            return False
        from django.utils import timezone
        return timezone.now() >= self.expires_at
    
    def needs_refresh(self):
        if not self.expires_at:
            return False
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() >= (self.expires_at - timedelta(minutes=5))
