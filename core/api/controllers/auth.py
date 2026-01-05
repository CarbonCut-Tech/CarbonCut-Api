import logging
from django.views import View
from django.shortcuts import redirect
from django.conf import settings
from pydantic import ValidationError
from django.http import  HttpRequest
from apps.common.response import response_factory
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from core.services.auth.otp_service import OTPService
from core.services.auth.jwt_service import JWTService
from core.services.auth.user_service import UserService
from core.services.auth.oauth_service import GoogleOAuthService
from core.services.auth.credential_service import OAuthCredentialService

logger = logging.getLogger(__name__)

class AuthController:
    def __init__(self):
        self.user_service = UserService()
        self.otp_service = OTPService()
        self.jwt_service = JWTService()
        self.oauth_service = GoogleOAuthService()
        self.credential_service = OAuthCredentialService()

@method_decorator(csrf_exempt, name='dispatch')
class SendOTPView(View):
    def post(self, request: HttpRequest):
        from apps.auth.schemas import SendOTPRequest
        try:
            controller = AuthController()
            request_data = SendOTPRequest.parse_raw(request.body)
            
            logger.info(f"OTP request for email: {request_data.email}")
            otp = controller.otp_service.generate_otp()
            expiry = controller.otp_service.get_otp_expiry()

            user, is_new = controller.user_service.get_or_create_user(
                email=request_data.email,
                name=request_data.name
            )

            controller.user_service.update_user_otp(
                user, otp, expiry, request_data.name
            )
            email_sent = controller.otp_service.send_otp_email(
                request_data.email,
                request_data.name or "User",
                otp,
                request_data.isLogin
            )
            
            if email_sent:
                message = ('Login code sent successfully' 
                          if request_data.isLogin 
                          else 'OTP sent successfully')
                return response_factory(message=message)
            else:
                return response_factory(
                    message='Failed to send OTP',
                    status=500
                )
                
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return response_factory(
                message="Invalid request data",
                errors=e.errors(),
                status=400
            )
        except Exception as e:
            logger.error(f"Error in send_otp: {e}", exc_info=True)
            return response_factory(message="Internal server error", status=500)

@method_decorator(csrf_exempt, name='dispatch')
class MeView(View):
    def get(self, request: HttpRequest):
        try:
            controller = AuthController()
            user_id, payload = controller.jwt_service.decode_token_from_request(request)
            if not user_id:
                return response_factory(message="Unauthorized", status=401)

            user = controller.user_service.get_user_by_id(user_id)
            if not user:
                return response_factory(message="User not found", status=404)

            return response_factory(
                message="User fetched",
                data={
                    "userId": user.id,
                    "email": user.email,
                    "name": user.name,
                    "companyName": user.company_name,
                    "phoneNumber": user.phone_number,
                    "onboarded": user.onboarded,
                }
            )
        except Exception as e:
            logger.error(f"Error in me: {e}", exc_info=True)
            return response_factory(message="Internal server error", status=500)
        
@method_decorator(csrf_exempt, name='dispatch')
class SignUpView(View):
    def post(self, request: HttpRequest):
        from apps.auth.schemas import SignUpRequest
        
        try:
            controller = AuthController()
            request_data = SignUpRequest.parse_raw(request.body)
            
            logger.info(f"Signup request for email: {request_data.email}")
            
            user, error = controller.user_service.create_user(
                email=request_data.email,
                name=request_data.name,
                company_name=request_data.companyName,
                phone_number=request_data.phoneNumber
            )
            
            if error:
                return response_factory(message=error, status=400)

            token = controller.user_service.generate_auth_token(user)
            
            return response_factory(
                message="User created successfully",
                data={
                    "userId": user.id,
                    "email": user.email,
                    "name": user.name,
                    "companyName": user.company_name,
                    "phoneNumber": user.phone_number,
                    "auth_token": token,
                }
            )
            
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return response_factory(
                message="Invalid request data",
                errors=e.errors(),
                status=400
            )
        except Exception as e:
            logger.error(f"Error in signup: {e}", exc_info=True)
            return response_factory(message="Internal server error", status=500)

@method_decorator(csrf_exempt, name='dispatch')
class VerifyOTPView(View):
    def post(self, request: HttpRequest):
        from apps.auth.schemas import VerifyOTPRequest
        
        try:
            controller = AuthController()
            request_data = VerifyOTPRequest.parse_raw(request.body)
            
            logger.info(f"OTP verification for: {request_data.email}")

            user, error = controller.user_service.verify_user_otp(
                request_data.email,
                request_data.otp
            )
            
            if error:
                return response_factory(message=error, status=400)
            token = controller.user_service.generate_auth_token(user)
            
            return response_factory(
                message="OTP verified successfully",
                data={
                    "userId": user.id,
                    "auth_token": token,
                }
            )
            
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return response_factory(
                message="Invalid request data",
                errors=e.errors(),
                status=400
            )
        except Exception as e:
            logger.error(f"Error in verify_otp: {e}", exc_info=True)
            return response_factory(message="Internal server error", status=500)


@method_decorator(csrf_exempt, name='dispatch')
class GoogleOAuthRedirectView(View):
    def get(self, request: HttpRequest):
        try:
            controller = AuthController()
            authorization_url, state = controller.oauth_service.get_authorization_url()
            
            request.session['google_oauth_state'] = state
            request.session.modified = True
            
            return redirect(authorization_url)
            
        except Exception as e:
            logger.error(f"Error in OAuth redirect: {e}", exc_info=True)
            return response_factory(
                message="Failed to initialize OAuth flow",
                status=500
            )


@method_decorator(csrf_exempt, name='dispatch')
class GoogleOAuthCallbackView(View):
    def get(self, request: HttpRequest):
        from apps.auth.schemas import GoogleOAuthCallbackRequest
        
        try:
            controller = AuthController()
            request_data = GoogleOAuthCallbackRequest(
                code=request.GET.get('code'),
                error=request.GET.get('error'),
                state=request.GET.get('state')
            )
            
            frontend_callback_url = f"{settings.FRONTEND_URL}/settings/integrations"

            if request_data.error:
                logger.error(f"OAuth error: {request_data.error}")
                return redirect(f"{frontend_callback_url}?error={request_data.error}")
            
            if not request_data.code or not request_data.state:
                return redirect(f"{frontend_callback_url}?error=missing_parameters")
            
            session_state = request.session.get('google_oauth_state')
            is_valid, error = controller.oauth_service.validate_state(
                session_state, 
                request_data.state
            )
            
            if not is_valid:
                logger.error(f"State validation failed: {error}")
                return redirect(f"{frontend_callback_url}?error=csrf_check_failed")
            
            del request.session['google_oauth_state']
            
            user_id = request.session.get('google_oauth_user_id')
            if not user_id:
                return redirect(f"{frontend_callback_url}?error=not_authenticated")
            
            user = controller.user_service.get_user_by_id(user_id)
            if not user:
                return redirect(f"{frontend_callback_url}?error=user_not_found")
            
            tokens, error = controller.oauth_service.exchange_code_for_tokens(
                request_data.code
            )
            
            if error:
                logger.error(f"Token exchange failed: {error}")
                return redirect(f"{frontend_callback_url}?error=token_exchange_failed")
            
            user_info, error = controller.oauth_service.get_user_info(
                tokens['access_token']
            )
            
            if error:
                return redirect(f"{frontend_callback_url}?error=user_info_failed")

            customer_id = "1234567890"
            customer_data = {
                'name': 'Default Customer',
                'currency': 'USD',
                'timezone': 'America/New_York'
            }
            
            credential, error = controller.credential_service.save_google_ads_credential(
                user=user,
                tokens=tokens,
                user_info=user_info,
                customer_id=customer_id,
                customer_data=customer_data
            )
            
            if error:
                return redirect(f"{frontend_callback_url}?error=credential_save_failed")
        
            if 'google_oauth_user_id' in request.session:
                del request.session['google_oauth_user_id']
                request.session.modified = True
            
            logger.info(f"Google Ads connected for user: {user.email}")
            
            return redirect(f"{frontend_callback_url}?success=true&provider=google_ads")
            
        except Exception as e:
            logger.error(f"Error in OAuth callback: {e}", exc_info=True)
            frontend_callback_url = f"{settings.FRONTEND_URL}/settings/integrations"
            return redirect(f"{frontend_callback_url}?error=server_error")


@method_decorator(csrf_exempt, name='dispatch')
class GoogleAdsStatusView(View):
    def get(self, request: HttpRequest):
        try:
            controller = AuthController()
            
            user_id, payload = controller.jwt_service.decode_token_from_request(request)
            if not user_id:
                return response_factory(
                    data={'is_connected': False},
                    message="Not authenticated",
                    status=401
                )
            
            user = controller.user_service.get_user_by_id(user_id)
            if not user:
                return response_factory(
                    data={'is_connected': False},
                    message="User not found",
                    status=404
                )
            
            credential, error = controller.credential_service.get_credential(user)
            
            if error:
                return response_factory(
                    data={'is_connected': False},
                    message=error
                )
            
            return response_factory(
                data={
                    'is_connected': True,
                    'customer_id': credential.extras.get('customer_id'),
                    'customer_name': credential.extras.get('customer_name'),
                    'email': credential.extras.get('email'),
                    'connected_at': credential.created_at.isoformat(),
                },
                message="Google Ads status fetched"
            )
            
        except Exception as e:
            logger.error(f"Error fetching status: {e}", exc_info=True)
            return response_factory(message="Failed to fetch status", status=500)


@method_decorator(csrf_exempt, name='dispatch')
class GoogleAdsDisconnectView(View):
    def post(self, request: HttpRequest):
        try:
            controller = AuthController()
            user_id, payload = controller.jwt_service.decode_token_from_request(request)
            if not user_id:
                return response_factory(message="Unauthorized", status=401)
            
            user = controller.user_service.get_user_by_id(user_id)
            if not user:
                return response_factory(message="User not found", status=404)
            
            success, error = controller.credential_service.disconnect_credential(user)
            
            if not success:
                return response_factory(message=error, status=404)
            
            return response_factory(message="Google Ads disconnected successfully")
            
        except Exception as e:
            logger.error(f"Error disconnecting: {e}", exc_info=True)
            return response_factory(message="Failed to disconnect", status=500)