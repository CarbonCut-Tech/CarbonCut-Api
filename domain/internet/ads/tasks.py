from celery import shared_task
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@shared_task
def poll_google_ads_task():
    from domain.internet.ads.poller import GoogleAdsPoller
    
    try:
        poller = GoogleAdsPoller()
        results = poller.poll_and_process()
        
        logger.info(
            f"Google Ads poll completed: {results['campaigns_processed']} campaigns, "
            f"{results['events_created']} events created"
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Error in Google Ads polling task: {e}", exc_info=True)
        raise