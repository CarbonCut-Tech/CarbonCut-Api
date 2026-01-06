from django.urls import path
from core.api.controllers.emission_reports import (
    EmissionSourcesConfigView,
    CloudCSVUploadView
)
from core.api.controllers.emission_reports import (
    EmissionSummaryView,
    EmissionsBySourceView,
    CSRDExportView
)

urlpatterns = [
    path('emission-sources/configure', EmissionSourcesConfigView.as_view(), name='emission_sources_configure'),
    path('emission-sources/config', EmissionSourcesConfigView.as_view(), name='emission_sources_config'),
    
    path('emission-sources/cloud/upload-csv', CloudCSVUploadView.as_view(), name='cloud_csv_upload'),
    path('emissions/summary', EmissionSummaryView.as_view(), name='emission_summary'),
    path('emissions/by-source', EmissionsBySourceView.as_view(), name='emissions_by_source'),
    path('emissions/export/csrd', CSRDExportView.as_view(), name='csrd_export'),
]