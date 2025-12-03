from django.db import models
from django.contrib.auth.models import AbstractUser
from rest_framework_simplejwt.tokens import RefreshToken

import uuid
import secrets

from shared.models import BaseModel

class AuthType(models.TextChoices):
    Email = 'email', 'Email'
    Phone = 'phone', 'Phone'

class UserStatus(models.TextChoices):
    New = 'new', 'New'
    CodeVerified = 'code_verified', 'Code Verified'
    Done = 'done', 'Done'
    Photo_Done = 'photo_done', 'Photo Done'


class User(AbstractUser, BaseModel):
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=13, unique=True, null=True, blank=True)
    auth_type = models.CharField(choices=AuthType.choices)
    user_status = models.CharField(choices=UserStatus.choices, default=UserStatus.New)
    photo = models.ImageField(upload_to='user_photos/', null=True, blank=True)

    def normalize_email(self):
        if self.email:
            self.email = self.email.lower().strip()
    
    def change_username(self):
       if not self.username:
           temp_username = f'instagram-{uuid.uuid4().__str__().split("-")[-1]}'
           while User.objects.filter(username=temp_username).exists():
                temp_username += str(secrets.randbelow(1000))
           self.username = temp_username
            
    def change_password(self):
        if not self.password:
            self.set_password(f"password-{uuid.uuid4().__str__().split('-')[-1]}")

    def generate_code(self, auth_type):
        code = ''.join(secrets.choice('0123456789') for _ in range(4))
        return UserConfirmation.objects.create(user=self, code=code, auth_type=auth_type)
    
    def token(self):
        refresh = RefreshToken.for_user(self)
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        return data
    
    
    def save(self, *args, **kwargs):
        
        self.normalize_email()
        self.change_username()
        self.change_password()
        super().save(*args, **kwargs)
    
PHONE_TIME = 3  # minutes
EMAIL_TIME = 5  # minutes

class UserConfirmation(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='confirmations')
    code = models.CharField(max_length=6)
    auth_type = models.CharField(choices=AuthType.choices)
    is_verified = models.BooleanField(default=False)
    expired_time = models.DateTimeField()

    def __str__(self):
        return f'Confirmation for {self.user.username} - Code: {self.code} - Verified: {self.is_verified}'
    
    def save(self, *args, **kwargs):
        
        from django.utils import timezone
        from datetime import timedelta
        expired_minutes = PHONE_TIME if self.auth_type == AuthType.Phone else EMAIL_TIME
        self.expired_time = timezone.now() + timedelta(minutes=expired_minutes)
        super().save(*args, **kwargs)
