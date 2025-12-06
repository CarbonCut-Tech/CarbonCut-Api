import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, TypedDict
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class IEAGridData(TypedDict):
    ISO3: str
    Date: str
    DayType: str
    Value: float


class GridIntensityResult(TypedDict):
    country: str
    iso3: str
    averageIntensity: float
    currentHourIntensity: float
    dataSource: str  
    lastUpdated: str

class GridIntensityService:
    IEA_API_BASE = 'https://api.iea.org/rte/co2/hourly'
    CACHE_DURATION = 60 * 60  
    REQUEST_TIMEOUT = 10
    
    COUNTRY_ISO_MAP = {
        'Austria': 'AUT', 'Belgium': 'BEL', 'Bulgaria': 'BGR', 'Croatia': 'HRV',
        'Cyprus': 'CYP', 'Czech Republic': 'CZE', 'Denmark': 'DNK', 'Estonia': 'EST',
        'Finland': 'FIN', 'France': 'FRA', 'Germany': 'DEU', 'Greece': 'GRC',
        'Hungary': 'HUN', 'Iceland': 'ISL', 'Ireland': 'IRL', 'Italy': 'ITA',
        'Latvia': 'LVA', 'Lithuania': 'LTU', 'Luxembourg': 'LUX', 'Malta': 'MLT',
        'Netherlands': 'NLD', 'Norway': 'NOR', 'Poland': 'POL', 'Portugal': 'PRT',
        'Romania': 'ROU', 'Slovakia': 'SVK', 'Slovenia': 'SVN', 'Spain': 'ESP',
        'Sweden': 'SWE', 'Switzerland': 'CHE', 'United Kingdom': 'GBR',
        
        'United States': 'USA', 'Canada': 'CAN', 'Mexico': 'MEX',
        
        'Argentina': 'ARG', 'Brazil': 'BRA', 'Chile': 'CHL', 'Colombia': 'COL',
        'Costa Rica': 'CRI', 'Uruguay': 'URY', 'Peru': 'PER', 'Ecuador': 'ECU',
        
        'Australia': 'AUS', 'China': 'CHN', 'India': 'IND', 'Indonesia': 'IDN',
        'Japan': 'JPN', 'South Korea': 'KOR', 'Malaysia': 'MYS', 'New Zealand': 'NZL',
        'Philippines': 'PHL', 'Singapore': 'SGP', 'Taiwan': 'TWN', 'Thailand': 'THA',
        'Vietnam': 'VNM', 'Bangladesh': 'BGD', 'Pakistan': 'PAK', 'Sri Lanka': 'LKA',
        
        'Egypt': 'EGY', 'Israel': 'ISR', 'Jordan': 'JOR', 'Morocco': 'MAR',
        'Nigeria': 'NGA', 'Saudi Arabia': 'SAU', 'South Africa': 'ZAF',
        'Turkey': 'TUR', 'UAE': 'ARE', 'Qatar': 'QAT', 'Kuwait': 'KWT',
        'Kenya': 'KEN', 'Ghana': 'GHA', 'Ethiopia': 'ETH',
    }

    # Fallback intensities (gCO2/kWh) - Based on 2023-2024 data
    FALLBACK_INTENSITIES = {
        'Norway': 14, 'Iceland': 21, 'Costa Rica': 18, 'Uruguay': 38,
        'France': 52, 'Sweden': 45, 'Switzerland': 38,
        
        'Finland': 103, 'Denmark': 89, 'New Zealand': 74, 'Austria': 76,
        'Brazil': 76, 'Canada': 98, 'Portugal': 145, 'Spain': 138,
        
        'Belgium': 168, 'United Kingdom': 212, 'Italy': 208, 'Ireland': 234,
        'Netherlands': 234, 'Slovenia': 178, 'Slovakia': 156, 'Latvia': 145,
        'Lithuania': 198, 'Romania': 267, 'Chile': 267,
        
        'Germany': 298, 'United States': 389, 'Japan': 456, 'Turkey': 398,
        'Mexico': 378, 'Greece': 398, 'Croatia': 345, 'Hungary': 312,
        'Argentina': 334, 'Czech Republic': 367, 'South Korea': 423,
        'Thailand': 398, 'Singapore': 376, 'Malaysia': 456, 'Israel': 467,        

        'Poland': 612, 'Australia': 534, 'China': 578, 'India': 642,
        'South Africa': 756, 'Indonesia': 634, 'Vietnam': 567,
        'Taiwan': 498, 'Philippines': 534, 'Morocco': 534, 'Egypt': 498,
        'Saudi Arabia': 456, 'UAE': 423, 'Kuwait': 534, 'Qatar': 445,
        'Nigeria': 567, 'Kenya': 378, 'Ghana': 445, 'Pakistan': 512,
        'Bangladesh': 598, 'Sri Lanka': 423, 'Jordan': 512,
        
        # Global average
        'default': 475  
    }
    
    @classmethod
    async def get_grid_intensity(cls, country: str) -> GridIntensityResult:
        try:
            country = country.strip()
            cache_key = f"grid_intensity_{country.lower().replace(' ', '_')}"
            
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for {country}: {cached_data['averageIntensity']} gCO2/kWh")
                return cached_data
            
            iso3 = cls.COUNTRY_ISO_MAP.get(country)
            if not iso3:
                logger.warning(f"No ISO3 mapping for '{country}', using fallback")
                return cls._get_fallback_intensity(country)
            
            result = await cls._fetch_from_iea(country, iso3)
            
            cache.set(cache_key, result, cls.CACHE_DURATION)
            
            return result
            
        except Exception as error:
            logger.error(f"Error fetching grid intensity for {country}: {error}", exc_info=True)
            return cls._get_fallback_intensity(country)
    
    @classmethod
    async def _fetch_from_iea(cls, country: str, iso3: str) -> GridIntensityResult:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        from_date = start_date.strftime('%Y-%m-%d')
        to_date = end_date.strftime('%Y-%m-%d')
        
        url = f"{cls.IEA_API_BASE}/{iso3}/timeseries?from={from_date}&to={to_date}&co2Metric=average"
        
        logger.info(f"Fetching IEA data for {country} ({iso3})")
        
        timeout = aiohttp.ClientTimeout(total=cls.REQUEST_TIMEOUT)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'CarbonCut-Calculator/1.0'
            }
            
            async with session.get(url, headers=headers) as response:
                if not response.ok:
                    raise Exception(f"IEA API error: {response.status} {response.reason}")
                
                data: List[IEAGridData] = await response.json()
                
                if not data or len(data) == 0:
                    raise Exception('No data from IEA API')
                
                total_intensity = sum(item['Value'] for item in data)
                average_intensity = round(total_intensity / len(data))
                
                current_hour = datetime.now().hour
                current_hour_data = next(
                    (item for item in data 
                     if 'h' in item['Date'] and int(item['Date'].replace('h', '')) == current_hour),
                    None
                )
                
                current_hour_intensity = (
                    round(current_hour_data['Value']) 
                    if current_hour_data 
                    else average_intensity
                )
                
                logger.info(
                    f"IEA: {country} avg={average_intensity}, current={current_hour_intensity} gCO2/kWh"
                )
                return GridIntensityResult({
                    'country': country,
                    'iso3': iso3,
                    'averageIntensity': average_intensity,
                    'currentHourIntensity': current_hour_intensity,
                    'dataSource': 'IEA_API',
                    'lastUpdated': datetime.now().isoformat()
                })
    
    @classmethod
    def _get_fallback_intensity(cls, country: str) -> GridIntensityResult:
        intensity = cls.FALLBACK_INTENSITIES.get(country, cls.FALLBACK_INTENSITIES['default'])
        
        logger.info(f"Fallback for {country}: {intensity} gCO2/kWh")
        
        return GridIntensityResult({
            'country': country,
            'iso3': cls.COUNTRY_ISO_MAP.get(country, 'UNK'),
            'averageIntensity': intensity,
            'currentHourIntensity': intensity,
            'dataSource': 'FALLBACK',
            'lastUpdated': datetime.now().isoformat()
        })
    
    @classmethod
    def clear_cache(cls, country: Optional[str] = None) -> None:
        if country:
            cache_key = f"grid_intensity_{country.lower().replace(' ', '_')}"
            cache.delete(cache_key)
            logger.info(f'Cache cleared for {country}')
        else:
            cache_keys = [
                f"grid_intensity_{country.lower().replace(' ', '_')}" 
                for country in cls.COUNTRY_ISO_MAP.keys()
            ]
            cache.delete_many(cache_keys)
            logger.info('All grid intensity cache cleared')
    
    @classmethod
    def get_cache_status(cls) -> Dict[str, any]:
        cached_countries = []
        for country in cls.COUNTRY_ISO_MAP.keys():
            cache_key = f"grid_intensity_{country.lower().replace(' ', '_')}"
            if cache.get(cache_key):
                cached_countries.append(country)
        
        return {
            'total_countries': len(cls.COUNTRY_ISO_MAP),
            'cached_count': len(cached_countries),
            'cached_countries': cached_countries,
            'cache_hit_rate': f"{(len(cached_countries) / len(cls.COUNTRY_ISO_MAP) * 100):.1f}%"
        }


def get_grid_intensity_sync(country: str) -> GridIntensityResult:
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        
        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    GridIntensityService.get_grid_intensity(country)
                )
                return future.result(timeout=15)
        else:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(
                    GridIntensityService.get_grid_intensity(country)
                )
            finally:
                new_loop.close()
                
    except Exception as e:
        logger.error(f"Error in sync grid intensity fetch: {e}", exc_info=True)
        return GridIntensityService._get_fallback_intensity(country)