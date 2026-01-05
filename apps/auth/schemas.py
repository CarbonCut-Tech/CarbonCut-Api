from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class SendOTPRequest(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    isLogin: bool = False

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str


class SendOTPResponse(BaseModel):
    success: bool
    message: str

class VerifyOTPResponse(BaseModel):
    success: bool
    message: str
    userId: Optional[str] = None
    auth_token: Optional[str] = None

class UserData(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str]
    companyName: Optional[str]
    phoneNumber: Optional[str]

class OnboardingStatusResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str] = None  
    phonenumber: Optional[str] = None  
    companyname: Optional[str] = None  
    createdat: str  
    updatedat: str  
    otpverified: bool
    isactive: bool
    onboarded: bool

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class GoogleOAuthCallbackRequest(BaseModel):
    code: Optional[str] = None
    error: Optional[str] = None
    state: Optional[str] = None

class GoogleAdsConnectionResponse(BaseModel):
    success: bool
    message: str
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    email: Optional[str] = None

class SignUpRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    companyName: str = Field(..., min_length=1, max_length=255)
    phoneNumber: str = Field(..., min_length=5, max_length=20)