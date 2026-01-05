from decimal import Decimal
from typing import Dict, Any
from enum import Enum
from .base import BaseEmissionCalculator


class AdFormat(str, Enum):
    STATIC_DISPLAY = 'static_display'
    RICH_MEDIA = 'rich_media'
    VIDEO = 'video'


class Platform(str, Enum):
    GOOGLE_ADS = 'google_ads'
    DV360 = 'dv360'
    META = 'meta'
    TIKTOK = 'tiktok'
    SNAPCHAT = 'snapchat'
    LINKEDIN = 'linkedin'
    TWITTER_X = 'twitter_x'
    DSP_GENERIC = 'dsp_generic'


class InternetAdsCalculator(BaseEmissionCalculator):
    VERSION = "2025.1"
    
    E_ADSERV = {
        Platform.GOOGLE_ADS: {
            AdFormat.STATIC_DISPLAY: Decimal('0.0005'),
            AdFormat.RICH_MEDIA: Decimal('0.0020'),
            AdFormat.VIDEO: Decimal('0.0120'),
        },
        Platform.DV360: {
            AdFormat.STATIC_DISPLAY: Decimal('0.0005'),
            AdFormat.RICH_MEDIA: Decimal('0.0020'),
            AdFormat.VIDEO: Decimal('0.0120'),
        },
        Platform.META: {
            AdFormat.STATIC_DISPLAY: Decimal('0.0005'),
            AdFormat.RICH_MEDIA: Decimal('0.0015'),
            AdFormat.VIDEO: Decimal('0.0020'),
        },
        Platform.TIKTOK: {
            AdFormat.VIDEO: Decimal('0.0120'),
        },
        Platform.SNAPCHAT: {
            AdFormat.VIDEO: Decimal('0.0020'),
        },
        Platform.LINKEDIN: {
            AdFormat.STATIC_DISPLAY: Decimal('0.0004'),
            AdFormat.RICH_MEDIA: Decimal('0.0010'),
        },
        Platform.TWITTER_X: {
            AdFormat.STATIC_DISPLAY: Decimal('0.0010'),
            AdFormat.RICH_MEDIA: Decimal('0.0015'),
        },
        Platform.DSP_GENERIC: {
            AdFormat.STATIC_DISPLAY: Decimal('0.0007'),
            AdFormat.RICH_MEDIA: Decimal('0.0015'),
            AdFormat.VIDEO: Decimal('0.0020'),
        },
    }
    
    E_CDN = {
        Platform.GOOGLE_ADS: {
            AdFormat.STATIC_DISPLAY: Decimal('0.0006'),
            AdFormat.RICH_MEDIA: Decimal('0.0008'),
            AdFormat.VIDEO: Decimal('0.0010'),
        },
        Platform.META: {
            AdFormat.STATIC_DISPLAY: Decimal('0.0003'),
            AdFormat.RICH_MEDIA: Decimal('0.0004'),
            AdFormat.VIDEO: Decimal('0.0005'),
        },
        Platform.TIKTOK: {
            AdFormat.VIDEO: Decimal('0.0010'),
        },
        Platform.SNAPCHAT: {
            AdFormat.VIDEO: Decimal('0.0010'),
        },
        Platform.LINKEDIN: {
            AdFormat.STATIC_DISPLAY: Decimal('0.0004'),
            AdFormat.RICH_MEDIA: Decimal('0.0005'),
        },
        Platform.TWITTER_X: {
            AdFormat.STATIC_DISPLAY: Decimal('0.0006'),
            AdFormat.RICH_MEDIA: Decimal('0.0007'),
        },
        Platform.DSP_GENERIC: {
            AdFormat.STATIC_DISPLAY: Decimal('0.0008'),
            AdFormat.RICH_MEDIA: Decimal('0.0009'),
            AdFormat.VIDEO: Decimal('0.0010'),
        },
    }
    
    E_NETWORK = {
        AdFormat.STATIC_DISPLAY: Decimal('0.00006'),
        AdFormat.RICH_MEDIA: Decimal('0.00020'),
        AdFormat.VIDEO: Decimal('0.00100'),
    }
    
    E_TRACK_WH_PER_CLICK = Decimal('0.0003')
    E_SERVER_W = Decimal('100')
    T_PROC_H = Decimal('0.001')
    E_DATA_WH_PER_MB = Decimal('0.20')
    V_TRANS_MB = Decimal('0.1')
    
    E_DEVICE_W = {
        'mobile': Decimal('2.0'),
        'desktop': Decimal('60.0'),
        'tablet': Decimal('8.0'),
    }
    
    T_DWELL_S = {
        AdFormat.STATIC_DISPLAY: Decimal('2'),
        AdFormat.RICH_MEDIA: Decimal('5'),
        AdFormat.VIDEO: Decimal('15'),
    }
    
    GRID_INTENSITY_DEFAULTS = {
        'GB': Decimal('233'),
        'US': Decimal('417'),
        'DE': Decimal('385'),
        'FR': Decimal('57'),
        'EU': Decimal('295'),
        'WORLD': Decimal('475'),
    }
    
    def calculate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        platform = self._get_platform(input_data)
        ad_format = self._get_ad_format(input_data)
        impressions = self._to_decimal(input_data.get('impressions', 0))
        clicks = self._to_decimal(input_data.get('clicks', 0))
        conversions = self._to_decimal(input_data.get('conversions', 0))
        device_type = input_data.get('device_type', 'desktop').lower()
        region = input_data.get('country_code', 'US').upper()
        
        grid_ef_kg_per_kwh = self._get_grid_emission_factor(region)
        
        e_adserv = self._get_coefficient(self.E_ADSERV, platform, ad_format, Decimal('0.0010'))
        e_cdn = self._get_coefficient(self.E_CDN, platform, ad_format, Decimal('0.0008'))
        e_network = self.E_NETWORK.get(ad_format, Decimal('0.00020'))
        
        e_upstream_per_imp_wh = e_adserv + e_cdn + e_network
        total_imp_energy_kwh = (e_upstream_per_imp_wh * impressions) / Decimal('1000')
        co2e_impressions_kg = total_imp_energy_kwh * grid_ef_kg_per_kwh
        
        total_click_energy_kwh = (self.E_TRACK_WH_PER_CLICK * clicks) / Decimal('1000')
        co2e_clicks_kg = total_click_energy_kwh * grid_ef_kg_per_kwh
        
        e_server_kwh = (self.E_SERVER_W * self.T_PROC_H) / Decimal('1000')
        e_data_kwh = (self.E_DATA_WH_PER_MB * self.V_TRANS_MB) / Decimal('1000')
        e_conversion_kwh = e_server_kwh + e_data_kwh
        total_conv_energy_kwh = e_conversion_kwh * conversions
        co2e_conversions_kg = total_conv_energy_kwh * grid_ef_kg_per_kwh
        
        upstream_total_kg = co2e_impressions_kg + co2e_clicks_kg + co2e_conversions_kg
        
        e_device_w = self.E_DEVICE_W.get(device_type, self.E_DEVICE_W['desktop'])
        t_dwell_s = self.T_DWELL_S.get(ad_format, Decimal('5'))
        t_dwell_h = t_dwell_s / Decimal('3600')
        
        device_energy_per_imp_kwh = (e_device_w * t_dwell_h) / Decimal('1000')
        total_downstream_kwh = device_energy_per_imp_kwh * impressions
        downstream_total_kg = total_downstream_kwh * grid_ef_kg_per_kwh
        
        return {
            'total_emissions_kg': float(upstream_total_kg),
            'total_emissions_g': float(upstream_total_kg * 1000),
            'breakdown': {
                'upstream_total_kg': float(upstream_total_kg),
                'impressions_kg': float(co2e_impressions_kg),
                'clicks_kg': float(co2e_clicks_kg),
                'conversions_kg': float(co2e_conversions_kg),
                'adserving_kg': float((e_adserv * impressions / 1000) * grid_ef_kg_per_kwh),
                'cdn_kg': float((e_cdn * impressions / 1000) * grid_ef_kg_per_kwh),
                'network_kg': float((e_network * impressions / 1000) * grid_ef_kg_per_kwh),
                'downstream_total_kg': float(downstream_total_kg),
                'user_device_kg': float(downstream_total_kg),
            },
            'methodology': {
                'version': self.VERSION,
                'platform': platform.value,
                'ad_format': ad_format.value,
                'region': region,
                'source': self._get_ef_source(region),
                'grid_ef_kg_per_kwh': float(grid_ef_kg_per_kwh),
                'e_adserv_wh_per_imp': float(e_adserv),
                'e_cdn_wh_per_imp': float(e_cdn),
                'e_network_wh_per_imp': float(e_network),
                'e_upstream_total_wh_per_imp': float(e_upstream_per_imp_wh),
                'e_track_wh_per_click': float(self.E_TRACK_WH_PER_CLICK),
                'e_server_w': float(self.E_SERVER_W),
                't_proc_h': float(self.T_PROC_H),
                'e_data_wh_per_mb': float(self.E_DATA_WH_PER_MB),
                'v_trans_mb': float(self.V_TRANS_MB),
                'device_type': device_type,
                'e_device_w': float(e_device_w),
                't_dwell_s': float(t_dwell_s),
            },
            
            'factors': {
                'impressions': float(impressions),
                'clicks': float(clicks),
                'conversions': float(conversions),
                'platform': platform.value,
                'ad_format': ad_format.value,
                'device_type': device_type,
                'country': region,
            }
        }
    
    def _get_ad_format(self, input_data: Dict[str, Any]) -> AdFormat:
        format_str = input_data.get('ad_format', 'static_display').lower()
        
        format_map = {
            'static': AdFormat.STATIC_DISPLAY,
            'static_display': AdFormat.STATIC_DISPLAY,
            'display': AdFormat.STATIC_DISPLAY,
            'rich': AdFormat.RICH_MEDIA,
            'rich_media': AdFormat.RICH_MEDIA,
            'video': AdFormat.VIDEO,
        }
        
        return format_map.get(format_str, AdFormat.STATIC_DISPLAY)
    
    def _get_platform(self, input_data: Dict[str, Any]) -> Platform:
        platform_str = input_data.get('platform', 'google_ads').lower()
        
        platform_map = {
            'google': Platform.GOOGLE_ADS,
            'google_ads': Platform.GOOGLE_ADS,
            'gads': Platform.GOOGLE_ADS,
            'dv360': Platform.DV360,
            'meta': Platform.META,
            'facebook': Platform.META,
            'instagram': Platform.META,
            'tiktok': Platform.TIKTOK,
            'snapchat': Platform.SNAPCHAT,
            'snap': Platform.SNAPCHAT,
            'linkedin': Platform.LINKEDIN,
            'twitter': Platform.TWITTER_X,
            'x': Platform.TWITTER_X,
            'dsp': Platform.DSP_GENERIC,
        }
        
        return platform_map.get(platform_str, Platform.GOOGLE_ADS)
    
    def _get_coefficient(
        self,
        coeff_dict: Dict,
        platform: Platform,
        ad_format: AdFormat,
        default: Decimal
    ) -> Decimal:
        try:
            return coeff_dict[platform][ad_format]
        except KeyError:
            try:
                return coeff_dict[Platform.DSP_GENERIC][ad_format]
            except KeyError:
                return default
    
    def _get_grid_emission_factor(self, region: str) -> Decimal:
        grid_intensity_g = self.GRID_INTENSITY_DEFAULTS.get(
            region,
            self.GRID_INTENSITY_DEFAULTS['WORLD']
        )
        return grid_intensity_g / Decimal('1000')
    
    def _get_ef_source(self, region: str) -> str:
        sources = {
            'GB': 'UK BEIS 2023 via IEA',
            'US': 'EPA eGRID 2023',
            'DE': 'IEA 2023',
            'FR': 'IEA 2023',
            'EU': 'IEA 2023',
        }
        return sources.get(region, 'IEA 2023 World Average')