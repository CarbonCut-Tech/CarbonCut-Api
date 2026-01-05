from datetime import datetime, timedelta
from typing import Optional, Tuple
import random
import re
import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

class OTPService:
    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 10
    
    def generate_otp(self) -> str:
        return str(random.randint(100000, 999999))
    
    def get_otp_expiry(self) -> datetime:
        return timezone.now() + timedelta(minutes=self.OTP_EXPIRY_MINUTES)
    
    def validate_email(self, email: str) -> bool:
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        return re.match(email_regex, email) is not None
    
    def send_otp_email(
        self, 
        email: str, 
        name: str, 
        otp: str, 
        is_login: bool = False
    ) -> bool:
        try:
            context = {
                "name": name,
                "otp": otp,
                "is_login": is_login,
            }
            
            html_message = render_to_string("auth/templates/otp.html", context)
            
            send_mail(
                subject="Your OTP Code" if not is_login else "Your Login Code",
                message="",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
            )
            
            logger.info(f"OTP email sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send OTP email: {e}", exc_info=True)
            return False
    
    def verify_otp(
        self, 
        stored_otp: Optional[str], 
        stored_expiry: Optional[datetime],
        provided_otp: str
    ) -> Tuple[bool, Optional[str]]:
        if not stored_otp:
            return False, "No OTP found"
        
        if not stored_expiry or stored_expiry < timezone.now():
            return False, "OTP has expired"
        
        if stored_otp != provided_otp:
            return False, "Invalid OTP"
        
        return True, None