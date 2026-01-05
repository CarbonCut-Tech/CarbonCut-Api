from django.contrib import admin
from .models import Campaign, UTMParameter, CampaignEmission
@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'google_ads_campaign_id', 'total_impressions', 'total_emissions_kg', 'created_at']
    list_filter = ['is_archived', 'created_at']
    search_fields = ['name', 'user__email', 'google_ads_campaign_id']
    readonly_fields = ['external_id', 'created_at', 'updated_at']
    
@admin.register(UTMParameter)
class UTMParameterAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'key', 'value', 'user']
    list_filter = ['key']
    search_fields = ['campaign__name', 'value']
    
@admin.register(CampaignEmission)
class CampaignEmissionAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'date', 'country', 'device_type', 'impressions', 'total_emissions_g']
    list_filter = ['date', 'country', 'device_type']
    search_fields = ['campaign__name']
    readonly_fields = ['external_id', 'created_at', 'updated_at']