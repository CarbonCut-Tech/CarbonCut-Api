from datetime import timedelta, datetime
from django.core.mail import send_mail
from django.utils.timezone import now
from django.template.loader import render_to_string
from django.conf import settings
import re
import random
import os

class OTPService:
    @staticmethod
    def generate_otp() -> str:
        return str(random.randint(100000, 999999))
    
    @staticmethod
    def validate_email(email: str) -> bool:
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        return re.match(email_regex, email) is not None
     
    @staticmethod
    def send_otp_email(email: str, name: str, otp: str, is_login: bool = False) -> bool:
        context = {
            "name": name,
            "otp": otp,
            "is_login": is_login,
        }
        html_message = render_to_string("auth/ejs/otp.html", context)
        send_mail(
            subject="Your OTP Code",
            message="",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
        )
        return True
    
    @staticmethod
    def get_otp_expiry() -> 'datetime':
        return now() + timedelta(minutes=10)