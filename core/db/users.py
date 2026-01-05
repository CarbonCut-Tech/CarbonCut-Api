from typing import Optional, Tuple
from datetime import datetime
from core.models.user import User, OAuthCredential
import logging

logger = logging.getLogger(__name__)

class UserData:
    def get_by_email(self, email: str) -> Optional[User]:
        from apps.auth.models import User as DjangoUser
        
        try:
            django_user = DjangoUser.objects.get(email=email)
            return self._to_domain(django_user)
        except DjangoUser.DoesNotExist:
            return None
    
    def create(self, email: str, name: Optional[str] = None, 
               company_name: Optional[str] = None, 
               phone_number: Optional[str] = None) -> User:
        from apps.auth.models import User as DjangoUser

        django_user = DjangoUser.objects.create(
            email=email,
            name=name or '',
            companyname=company_name or '',
            phonenumber=phone_number or ''
        )
        
        return self._to_domain(django_user)
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        from apps.auth.models import User as DjangoUser
        
        try:
            django_user = DjangoUser.objects.get(id=user_id)
            return self._to_domain(django_user)
        except DjangoUser.DoesNotExist:
            return None
    
    def get_or_create(self, email: str, name: Optional[str] = None) -> Tuple[User, bool]:
        from apps.auth.models import User as DjangoUser
        
        django_user, created = DjangoUser.objects.get_or_create(
            email=email,
            defaults={'name': name or ''}
        )
        
        return self._to_domain(django_user), created
    
    def save(self, user: User) -> User:
        from apps.auth.models import User as DjangoUser
        
        django_user = DjangoUser.objects.get(id=user.id)
        django_user.name = user.name
        django_user.phonenumber = user.phone_number
        django_user.companyname = user.company_name
        django_user.otpcode = user.otp_code
        django_user.otpexpiry = user.otp_expiry
        django_user.otpverified = user.otp_verified
        django_user.isactive = user.is_active
        django_user.onboarded = user.onboarded
        django_user.save()
        
        return self._to_domain(django_user)
    
    def _to_domain(self, django_user) -> User:
        return User(
            id=str(django_user.id),
            email=django_user.email,
            name=django_user.name,
            phone_number=django_user.phonenumber,
            company_name=django_user.companyname,
            created_at=django_user.createdat,
            updated_at=django_user.updatedat,
            otp_code=django_user.otpcode,
            otp_expiry=django_user.otpexpiry,
            otp_verified=django_user.otpverified,
            is_active=django_user.isactive,
            onboarded=django_user.onboarded
        )


class CredentialData:
    def get_by_user_and_provider(self, user_id: str, provider: str) -> Optional[OAuthCredential]:
        from apps.auth.models import Credential
        
        try:
            cred = Credential.objects.get(user_id=user_id, provider=provider)
            return self._to_domain(cred)
        except Credential.DoesNotExist:
            return None
    
    def save(self, credential: OAuthCredential) -> OAuthCredential:
        from apps.auth.models import Credential
        
        cred, created = Credential.objects.update_or_create(
            user_id=credential.user_id,
            provider=credential.provider,
            defaults={
                'provider_user_id': credential.provider_user_id,
                'access_token': credential.access_token,
                'refresh_token': credential.refresh_token,
                'expires_at': credential.expires_at,
                'scopes': ','.join(credential.scopes) if credential.scopes else '',
                'extras': credential.extras,
            }
        )
        
        return self._to_domain(cred)
    
    def delete(self, user_id: str, provider: str) -> bool:
        from apps.auth.models import Credential
        
        try:
            cred = Credential.objects.get(user_id=user_id, provider=provider)
            cred.delete()
            return True
        except Credential.DoesNotExist:
            return False
    
    def _to_domain(self, cred) -> OAuthCredential:
        scopes = cred.scopes.split(',') if cred.scopes else []
        
        return OAuthCredential(
            id=str(cred.id),
            user_id=str(cred.user_id),
            provider=cred.provider,
            provider_user_id=cred.provider_user_id,
            access_token=cred.access_token,
            refresh_token=cred.refresh_token,
            expires_at=cred.expires_at,
            scopes=scopes,
            created_at=cred.created_at,
            updated_at=cred.updated_at,
            extras=cred.extras or {}
        )