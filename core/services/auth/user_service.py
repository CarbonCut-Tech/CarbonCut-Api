from typing import Optional, Tuple
from datetime import datetime
import logging
from core.models.user import User
from core.db.users import UserData
from core.services.auth.otp_service import OTPService
from core.services.auth.jwt_service import JWTService

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self):
        self.user_repo = UserData()
        self.otp_service = OTPService()
        self.jwt_service = JWTService()
    
    def get_or_create_user(
        self, 
        email: str, 
        name: Optional[str] = None
    ) -> Tuple[User, bool]:
        user, created = self.user_repo.get_or_create(email, name)
        
        if created:
            logger.info(f"New user created: {email}")
        else:
            logger.info(f"Existing user retrieved: {email}")
        
        return user, created
    
    def create_user(
        self,
        email: str,
        name: str,
        company_name: str,
        phone_number: str
    ) -> Tuple[Optional[User], Optional[str]]:
        existing_user = self.user_repo.get_by_email(email)
        if existing_user:
            return None, "User already exists with this email"
    
        try:
            user = self.user_repo.create(
                email=email,
                name=name,
                company_name=company_name,
                phone_number=phone_number
            )
            logger.info(f"User created via signup: {email}")
            return user, None
        except Exception as e:
            logger.error(f"Error creating user: {e}", exc_info=True)
        return None, "Failed to create user"
        
    def update_user_otp(
        self, 
        user: User, 
        otp: str, 
        expiry: datetime,
        name: Optional[str] = None
    ) -> User:
        user.otp_code = otp
        user.otp_expiry = expiry
        
        if name:
            user.name = name
        
        user.updated_at = datetime.now()
        
        return self.user_repo.save(user)
    
    def verify_user_otp(
        self, 
        email: str, 
        otp: str
    ) -> Tuple[Optional[User], Optional[str]]:
        user = self.user_repo.get_by_email(email)
        
        if not user:
            return None, "User not found"
        
        is_valid, error = self.otp_service.verify_otp(
            user.otp_code,
            user.otp_expiry,
            otp
        )
        
        if not is_valid:
            return None, error
        user.otp_code = None
        user.otp_expiry = None
        user.otp_verified = True
        user.updated_at = datetime.now()
        
        saved_user = self.user_repo.save(user)
        return saved_user, None
    
    def generate_auth_token(self, user: User) -> str:
        return self.jwt_service.create_token(user.id, user.email)
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.user_repo.get_by_id(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.user_repo.get_by_email(email)