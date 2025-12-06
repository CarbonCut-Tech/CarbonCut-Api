from .schemas import SendOTPRequest, SendOTPResponse, VerifyOTPRequest, VerifyOTPResponse, UserResponse, GoogleOAuthCallbackRequest, GoogleAdsConnectionResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .services.cookie_service import CookieService
from apps.common.response import response_factory
from .services.user_service import UserService
from .services.otp_services import OTPService
from .models import User
from django.conf import settings
from .services.jwt_service import JWTService
from .services.google_oauth_service import GoogleOAuthService
from .services.google_ads_credential_service import GoogleAdsCredentialService
from pydantic import ValidationError
from django.http import HttpRequest
from django.views import View
from django.shortcuts import redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import IsAuthenticated
import logging

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class SendOTPView(View):
    def post(self, request: HttpRequest):
        try:
            request_data = SendOTPRequest.parse_raw(request.body)
            
            logger.info(f"OTP request for email: {request_data.email}, isLogin: {request_data.isLogin}")

            otp = OTPService.generate_otp()
            expiry = OTPService.get_otp_expiry()
            
            logger.info(f"Generated OTP for {request_data.email}")
            
            user, is_new_user = UserService.get_or_create_user(
                email=request_data.email,
                name=request_data.name
            )
            
            UserService.update_user_otp(user, otp, expiry, request_data.name)

            email_sent = OTPService.send_otp_email(
                request_data.email,
                request_data.name or "User",
                otp,
                request_data.isLogin
            )

            if email_sent:
                message = ('Login code sent successfully to your email address.'
                          if request_data.isLogin
                          else 'OTP sent successfully to your email address.')
                return response_factory(message=message)
            else:
                response = SendOTPResponse(
                    success=False,
                    message='Failed to send OTP. Please try again.'
                )
                return response_factory(data=response.dict(), message=response.message, status=500)

        except ValidationError as e:
            logger.error(f"Validation error in send_otp: {e}")
            return response_factory(message="Invalid request data", errors=e.errors(), status=400)
        except Exception as e:
            logger.error(f"Error in send_otp: {e}", exc_info=True)
            return response_factory(message="Internal server error", status=500)


@method_decorator(csrf_exempt, name='dispatch')
class VerifyOTPView(View):
    def post(self, request: HttpRequest):
        try:
            request_data = VerifyOTPRequest.parse_raw(request.body)
            logger.info(f"OTP verification request for: {request_data.email}")

            user, error = UserService.verify_user_otp(request_data.email, request_data.otp)
            if error:
                response = VerifyOTPResponse(success=False, message=error)
                return response_factory(data=response.dict(), message=response.message, status=400)

            token = UserService.generate_auth_token(user)

            return response_factory(
                message="OTP verified successfully!",
                data={
                    "userId": str(user.id),
                    "auth_token": token,
                }
            )

        except ValidationError as e:
            logger.error(f"Validation error in verify_otp: {e}")
            return response_factory(message="Invalid request data", errors=e.errors(), status=400)
        except Exception as e:
            logger.error(f"Error in verify_otp: {e}", exc_info=True)
            return response_factory(message="Internal server error", status=500)
        
@method_decorator(csrf_exempt, name='dispatch')
class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]  

    def get(self, request):
        user = request.user
        user_data = UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            phonenumber=user.phonenumber,
            companyname=user.companyname,
            createdat=user.createdat.isoformat(),
            updatedat=user.updatedat.isoformat(),
            otpverified=user.otpverified,
            isactive=user.isactive,
            onboarded=user.onboarded,
        ).dict()

        return Response({
            "success": True,
            "message": "User fetched",
            "data": user_data
        })
    
@method_decorator(csrf_exempt,name="dispatch")
class LogoutUserView(View):
    def post(self,request:HttpRequest):
        logger.info("Logging Out User")
        
        response = response_factory(data={
            "success": True,
        }, message="User logged out successfully")
        
        CookieService.delete_auth_cookie(response=response)

        logger.info("Auth cookie deleted successfully")
        
        return response

@method_decorator(csrf_exempt, name='dispatch')
class GoogleOAuthRedirectView(View):
    def get(self, request: HttpRequest):
        try:
            # ✅ UNCOMMENT THIS - Extract user ID from token
            user_id, payload = JWTService.decode_token_from_request(request)
            if not user_id:
                return response_factory(message="Unauthorized", status=401)
            
            # ✅ UNCOMMENT THIS - Store user ID in session
            request.session['google_oauth_user_id'] = user_id

            authorization_url, state = GoogleOAuthService.get_authorization_url()
            
            request.session['google_oauth_state'] = state
            request.session.modified = True
            
            logger.info(f"Redirecting user {user_id} to Google OAuth")
            
            return redirect(authorization_url)
            
        except Exception as e:
            logger.error(f"Error in Google OAuth redirect: {e}", exc_info=True)
            return response_factory(message="Failed to initialize OAuth flow", status=500)


@method_decorator(csrf_exempt, name='dispatch')
class GoogleOAuthCallbackView(View):
    def get(self, request: HttpRequest):
        try:
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
                logger.error("Missing code or state parameter")
                return redirect(f"{frontend_callback_url}?error=missing_parameters")
            
            session_state = request.session.get('google_oauth_state')
            is_valid, error = GoogleOAuthService.validate_state(session_state, request_data.state)
            if not is_valid:
                logger.error(f"State validation failed: {error}")
                return redirect(f"{frontend_callback_url}?error=csrf_check_failed")
            
            del request.session['google_oauth_state']
            
            user_id = request.session.get('google_oauth_user_id')
            if not user_id:
                logger.error("No user ID in session")
                return redirect(f"{frontend_callback_url}?error=not_authenticated")
            
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.error(f"User {user_id} not found")
                return redirect(f"{frontend_callback_url}?error=user_not_found")
            
            tokens, error = GoogleOAuthService.exchange_code_for_tokens(request_data.code)
            if error:
                logger.error(f"Token exchange failed: {error}")
                return redirect(f"{frontend_callback_url}?error=token_exchange_failed")
            
            user_info, error = GoogleOAuthService.get_user_info(tokens['access_token'])
            if error:
                logger.error(f"Failed to get user info: {error}")
                return redirect(f"{frontend_callback_url}?error=user_info_failed")
            
            # TODO: Fetch Google Ads customer accounts
            customer_id = "1234567890"  
            customer_data = {
                'name': 'Default Customer',
                'currency': 'USD',
                'timezone': 'America/New_York'
            }
            
            credential, error = GoogleAdsCredentialService.save_credential(
                user=user,
                tokens=tokens,
                user_info=user_info,
                customer_id=customer_id,
                customer_data=customer_data
            )
            
            if error:
                logger.error(f"Failed to save credential: {error}")
                return redirect(f"{frontend_callback_url}?error=credential_save_failed")
            if 'google_oauth_user_id' in request.session:
                del request.session['google_oauth_user_id']
                request.session.modified = True
            
            logger.info(f"Google Ads connected successfully for user: {user.email}")
            
            return redirect(f"{frontend_callback_url}?success=true&provider=google_ads")
            
        except Exception as e:
            logger.error(f"Error in Google OAuth callback: {e}", exc_info=True)
            frontend_callback_url = f"{settings.FRONTEND_URL}/settings/integrations"
            return redirect(f"{frontend_callback_url}?error=server_error")


@method_decorator(csrf_exempt, name='dispatch')
class GoogleAdsStatusView(View):
    def get(self, request: HttpRequest):
        try:
            user_id, payload = JWTService.decode_token_from_request(request)
            if not user_id:
                return response_factory(
                    data={'is_connected': False},
                    message="Not authenticated",
                    status=401
                )
            
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return response_factory(
                    data={'is_connected': False},
                    message="User not found",
                    status=404
                )
            
            credential, error = GoogleAdsCredentialService.get_credential(user)
            
            if error:
                return response_factory(
                    data={'is_connected': False},
                    message=error
                )
            
            extras = credential.extras or {}
            
            return response_factory(
                data={
                    'is_connected': True,
                    'customer_id': extras.get('customer_id'),
                    'customer_name': extras.get('customer_name'),
                    'email': extras.get('email'),
                    'connected_at': credential.created_at.isoformat(),
                },
                message="Google Ads status fetched"
            )
            
        except Exception as e:
            logger.error(f"Error fetching Google Ads status: {e}", exc_info=True)
            return response_factory(message="Failed to fetch status", status=500)


@method_decorator(csrf_exempt, name='dispatch')
class GoogleAdsDisconnectView(View):
    def post(self, request: HttpRequest):
        try:
            user_id, payload = JWTService.decode_token_from_request(request)
            if not user_id:
                return response_factory(message="Unauthorized", status=401)
            
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return response_factory(message="User not found", status=404)
            
            success, error = GoogleAdsCredentialService.disconnect_credential(user)
            
            if not success:
                return response_factory(message=error, status=404)
            
            return response_factory(message="Google Ads disconnected successfully")
            
        except Exception as e:
            logger.error(f"Error disconnecting Google Ads: {e}", exc_info=True)
            return response_factory(message="Failed to disconnect", status=500)
