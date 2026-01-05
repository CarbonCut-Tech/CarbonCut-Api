from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Carbon Core'
    
    def ready(self):
        from domain.internet.web import processers as web_processers
        from domain.internet.ads import processers as ads_processers
        from domain.oil import processers as oil_processers
        
        from domain.registry import EventProcessorRegistry
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Registered event processors: {EventProcessorRegistry.list_event_types()}")