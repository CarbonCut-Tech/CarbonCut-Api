import logging
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from core.services.emission_reporting import EmissionReportingService
from core.services.emission_aggregator import EmissionAggregator
from core.services.auth.jwt_service import JWTService
from datetime import datetime
from core.services.cloud_csv_parser import AWSCCFTParser
from decimal import Decimal

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class EmissionSummaryView(View):
    def __init__(self):
        super().__init__()
        self.reporting_service = EmissionReportingService()
        self.aggregator = EmissionAggregator()
        self.jwt_service = JWTService()
    
    def get(self, request):
        try:
            user_id, payload = self.jwt_service.decode_token_from_request(request)
            if not user_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Unauthorized'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            month = int(request.GET.get('month', datetime.now().month))
            year = int(request.GET.get('year', datetime.now().year))
            recalculate = request.GET.get('recalculate', 'false').lower() == 'true'
            
            if not (1 <= month <= 12):
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid month. Must be between 1 and 12.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not (2020 <= year <= 2030):
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid year. Must be between 2020 and 2030.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Recalculate if requested
            if recalculate:
                logger.info(f"Recalculating emissions for {user_id}: {year}-{month:02d}")
                self.aggregator.calculate_monthly_emissions(user_id, month, year)
            
            report = self.reporting_service.generate_monthly_report(user_id, month, year)
            
            return JsonResponse({
                'success': True,
                'data': report
            })
            
        except Exception as e:
            logger.error(f"Error generating emission summary: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    def post(self, request):
        try:
            user_id, payload = self.jwt_service.decode_token_from_request(request)
            if not user_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Unauthorized'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            provider = request.POST.get('provider')
            uploaded_file = request.FILES.get('file')
            month = int(request.POST.get('month'))
            year = int(request.POST.get('year'))
            
            import os
            import tempfile
            
            temp_dir = tempfile.mkdtemp()
            file_path = os.path.join(temp_dir, uploaded_file.name)
            
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            if provider == 'aws':
                parser = AWSCCFTParser()
            #  to be done 
            # elif provider == 'gcp':
            #     parser = GCPCarbonParser()  
            # elif provider == 'azure':
            #     parser = AzureCarbonParser()  
            else:
                return JsonResponse({
                    'success': False,
                    'error': f'Unsupported provider: {provider}'
                }, status=400)
            
            # Parse
            parsed_data = parser.parse(file_path)
            
            # Store emissions in database
            from core.db.emission_sources import EmissionSourceData
            from datetime import date
            
            emission_data = EmissionSourceData()
            
            for record in parsed_data['records']:
                emission_data.record_emission(
                    user_id=user_id,
                    source_type=f'cloud_{provider}',
                    scope='scope_2',  # Cloud is Scope 2
                    kg_co2=Decimal(str(record['emissions_kg'])),
                    emission_date=date(year, month, 1),
                    reference_id=f"cloud_{provider}_{year}{month:02d}_{record['service']}",
                    metadata={
                        'service': record['service'],
                        'region': record['region'],
                        'emission_type': record['emission_type'],
                        'account_id': record.get('account_id'),
                        'model_version': record.get('model_version')
                    },
                    accuracy_level='high'  # Provider data!
                )
            
            # Mark CSV as uploaded
            from core.services.emission_source_service import EmissionSourceService
            emission_service = EmissionSourceService()
            emission_service.mark_csv_uploaded(
                user_id=user_id,
                provider=provider,
                csv_file_path=file_path
            )
            
            # Clean up
            os.remove(file_path)
            os.rmdir(temp_dir)
            
            return JsonResponse({
                'success': True,
                'message': f'Processed {len(parsed_data["records"])} records',
                'data': {
                    'total_emissions_kg': parsed_data['total_emissions_kg'],
                    'records_processed': parsed_data['record_count'],
                    'provider': provider,
                    'month': f'{year}-{month:02d}'
                }
            })
            
        except Exception as e:
            logger.error(f"Error uploading cloud CSV: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class EmissionsBySourceView(View):
    def __init__(self):
        super().__init__()
        self.reporting_service = EmissionReportingService()
        self.jwt_service = JWTService()
    
    def get(self, request):
        try:
            user_id, payload = self.jwt_service.decode_token_from_request(request)
            if not user_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Unauthorized'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            month = int(request.GET.get('month', datetime.now().month))
            year = int(request.GET.get('year', datetime.now().year))
            
            data = self.reporting_service.get_emissions_by_source(user_id, month, year)
            
            return JsonResponse({
                'success': True,
                'data': data
            })
            
        except Exception as e:
            logger.error(f"Error fetching emissions by source: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# @method_decorator(csrf_exempt, name='dispatch')
# class CSRDExportView(View):
#     def __init__(self):
#         super().__init__()
#         self.reporting_service = EmissionReportingService()
#         self.jwt_service = JWTService()
    
#     def _get_user_id_from_request(self, request) -> str:
#         auth_header = request.headers.get('Authorization', '')
#         if not auth_header.startswith('Bearer '):
#             raise ValueError("Invalid authorization header")
        
#         token = auth_header.replace('Bearer ', '')
#         payload = self.jwt_service.verify_token(token)
#         return payload.get('user_id')
    
#     def get(self, request):
#         try:
#             user_id = self._get_user_id_from_request(request)
            
#             year = int(request.GET.get('year', datetime.now().year))
#             export_format = request.GET.get('format', 'json').lower()
            
#             report = self.reporting_service.export_csrd_compliant(user_id, year)
            
#             if export_format == 'json':
#                 return JsonResponse({
#                     'success': True,
#                     'data': report
#                 })
#             elif export_format == 'csv':
#                 # Implement CSV export
#                 return JsonResponse({
#                     'success': False,
#                     'error': 'CSV export not yet implemented'
#                 }, status=status.HTTP_501_NOT_IMPLEMENTED)
#             else:
#                 return JsonResponse({
#                     'success': False,
#                     'error': 'Invalid format. Use json or csv.'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#         except Exception as e:
#             logger.error(f"Error exporting CSRD report: {e}", exc_info=True)
#             return JsonResponse({
#                 'success': False,
#                 'error': 'Internal server error'
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)