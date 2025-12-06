from ..models import User
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class UserService:
    @staticmethod
    def get_or_create_user(email: str, name: str = None):
        user, created = User.objects.get_or_create(
            email=email,
            defaults={'name': name or ''}
        )
        return user, created

    @staticmethod
    def update_user_otp(user: User, otp: str, expiry: timezone.now, name: str = None):
        user.otpcode = otp
        user.otpexpiry = expiry
        if name:
            user.name = name
        user.save()
        logger.info(f"Updated OTP for user {user.email}")

    @staticmethod
    def verify_user_otp(email: str, otp: str):
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None, "User not found"

        if not user.otpcode:
            return None, "No OTP found for this user"

        if user.otpexpiry < timezone.now():
            return None, "OTP has expired"

        if user.otpcode != otp:
            return None, "Invalid OTP"

        user.otpcode = None
        user.otpexpiry = None
        user.otpverified = True
        user.save()

        return user, None

    @staticmethod
    def generate_auth_token(user: User) -> str:
        import jwt
        from django.conf import settings
        from datetime import timedelta

        payload = {
            'user_id': str(user.id),
            'email': user.email,
            'exp': timezone.now() + timedelta(days=7)
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        return token
    
    @staticmethod
    def get_user_by_email(email):
        try:
            user = User.objects.get(email=email)
            return user, None
        except User.DoesNotExist:
            return None, "User not found"