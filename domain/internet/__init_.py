def autodiscover():
    from domain.internet.web import processers as web_processers
    from domain.internet.ads import processers as ads_processers

__all__ = ['autodiscover']