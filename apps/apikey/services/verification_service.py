import logging
import requests
from typing import Dict, List
from bs4 import BeautifulSoup
from django.conf import settings

logger = logging.getLogger(__name__)


class ScriptVerificationService:
    TRACKING_SCRIPT_CDN = getattr(settings, 'TRACKING_SCRIPT_CDN', 'https://cdn.jsdelivr.net/gh/rishi-optiminastic/cc-cdn@main/dist/carboncut.min.js?v=2')
    
    @staticmethod
    def verify_installation(url: str, api_key: str) -> Dict:
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'CarbonCut-Verification-Bot/1.0'
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')

            script_tags = soup.find_all('script')
            script_found = False
            api_key_valid = False
            
            for script in script_tags:
                src = script.get('src', '')
                if 'carboncut' in src.lower() or 'tracker' in src.lower():
                    script_found = True
                    
                script_content = script.string
                if script_content and api_key in script_content:
                    api_key_valid = True
            
            errors = []
            if not script_found:
                errors.append('Tracking script not found on the page')
            if not api_key_valid:
                errors.append('API key not found in script initialization')
            
            return {
                'installed': script_found and api_key_valid,
                'script_found': script_found,
                'api_key_valid': api_key_valid,
                'errors': errors if errors else None
            }
            
        except requests.RequestException as e:
            logger.error(f"Error verifying installation at {url}: {e}")
            return {
                'installed': False,
                'script_found': False,
                'api_key_valid': False,
                'errors': [f'Failed to fetch URL: {str(e)}']
            }

    @staticmethod
    def get_installation_instructions(api_key: str, domain: str) -> Dict:
        script_tag = f'''<script src="{ScriptVerificationService.TRACKING_SCRIPT_CDN}"></script>
<script>
  CarbonCutTracker.init({{
    apiKey: '{api_key}',
    domain: '{domain}',
    autoTrack: true
  }});
</script>'''
        
        npm_command = f"npm install @carboncut/tracker"
        
        installation_steps = [
            "1. Copy the script tag above",
            "2. Paste it before the closing </head> tag in your HTML",
            "3. Save and deploy your changes",
            "4. Test the installation using the verification tool"
        ]
        
        verification_url = f"{settings.FRONTEND_URL}/api-keys/verify"
        
        return {
            'script_tag': script_tag,
            'npm_command': npm_command,
            'installation_steps': installation_steps,
            'verification_url': verification_url
        }