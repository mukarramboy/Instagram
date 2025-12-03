from rest_framework import serializers
from .models import User, AuthType, UserStatus
from django.core.validators import FileExtensionValidator
from shared.utility import check_user_type
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import update_last_login
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from django.db.models import Q
from django.contrib.auth.password_validation import validate_password



class SignUpSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField(max_length=50)

    def validate_email_or_phone(self, value):
        value = value.lower()
        from shared.utility import email_or_phone_validator
        try:
            auth_type = email_or_phone_validator(value)
        except ValueError as e:
            raise ValidationError(str(e))
        self.context['auth_type'] = auth_type
        return value
    
    def validate(self, attrs):
        email_or_phone = attrs.get('email_or_phone')
        auth_type = self.context['auth_type']
        if auth_type == AuthType.Email:
            if User.objects.exclude(user_status=UserStatus.New).filter(email=email_or_phone).exists():
                raise ValidationError("User with this email already exists.")
        else:
            if User.objects.exclude(user_status=UserStatus.New).filter(phone_number=email_or_phone).exists():
                raise ValidationError("User with this phone number already exists.")
        return attrs
    
class VerifiedCodeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=4)

    def validate_code(self, value):
        if not value.isdigit() or len(value) != 4:
            raise ValidationError("Code must be a 4-digit number.")
        return value
    

class InformationUserSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
    first_name = serializers.CharField(max_length=150, required=True)
    password = serializers.CharField(max_length=128, required=True)
    confirm_password = serializers.CharField(max_length=128, required=True)

    def validate_username(self, value):
        user = self.context.get('request_user')
        if User.objects.exclude(id=user.id).filter(username=value).exists():
            raise ValidationError("Username is already taken.")
        return value
    
    def validate_first_name(self, value):
        if not value.isalpha():
            raise ValidationError("First name must contain only alphabetic characters.")
        return value

    def validate_last_name(self, value):
        if not value.isalpha():
            raise ValidationError("Last name must contain only alphabetic characters.")
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')
        if password != confirm_password:
            raise ValidationError("Passwords do not match.")
        return attrs
    
class UserPhotoSerializer(serializers.Serializer):
    photo = serializers.ImageField(validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])], required=False)

    def validate_photo(self, value):
        if value.size > 2 * 1024 * 1024:  # 2 MB limit
            raise ValidationError("Photo size should not exceed 2 MB.")
        return value
    


class LoginSerializer(TokenObtainPairSerializer):

    def __init__(self, *args, **kwargs):
        super(LoginSerializer, self).__init__(*args, **kwargs)
        self.fields['userinput'] = serializers.CharField(required=True)
        self.fields['username'] = serializers.CharField(required=False, read_only=True)

    def auth_validate(self, data):
        user_input = data.get('userinput')  # email, phone_number, username
        if check_user_type(user_input) == 'username':
            username = user_input
        elif check_user_type(user_input) == "email":  # Anora@gmail.com   -> anOra@gmail.com
            user = self.get_user(email__iexact=user_input) # user get method orqali user o'zgartiruvchiga biriktirildi
            username = user.username
        elif check_user_type(user_input) == 'phone':
            user = self.get_user(phone_number=user_input)
            username = user.username
        else:
            data = {
                'success': True,
                'message': "Siz email, username yoki telefon raqami jonatishingiz kerak"
            }
            raise ValidationError(data)

        authentication_kwargs = {
            self.username_field: username,
            'password': data['password']
        }
        # user statusi tekshirilishi kerak
        current_user = User.objects.filter(username__iexact=username).first()  # None

        if current_user is not None and current_user.auth_status in [UserStatus.NEW, UserStatus.CODE_VERIFIED]:
            raise ValidationError(
                {
                    'success': False,
                    'message': "Siz royhatdan toliq otmagansiz!"
                }
            )
        user = authenticate(**authentication_kwargs)
        if user is not None:
            self.user = user
        else:
            raise ValidationError(
                {
                    'success': False,
                    'message': "Sorry, login or password you entered is incorrect. Please check and trg again!"
                }
            )

    def validate(self, data):
        self.auth_validate(data)
        if self.user.auth_status not in [UserStatus.DONE, UserStatus.PHOTO_DONE]:
            raise ValidationError("Siz login qila olmaysiz. Ruxsatingiz yoq")
        data = self.user.token()
        data['auth_status'] = self.user.auth_status
        data['full_name'] = self.user.full_name
        return data

    def get_user(self, **kwargs):
        users = User.objects.filter(**kwargs)
        if not users.exists():
            raise ValidationError(
                {
                    "message": "No active account found"
                }
            )
        return users.first()


class LoginRefreshSerializer(TokenRefreshSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)
        access_token_instance = AccessToken(data['access'])
        user_id = access_token_instance['user_id']
        user = get_object_or_404(User, id=user_id)
        update_last_login(None, user)
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email_or_phone = attrs.get('email_or_phone', None)
        if email_or_phone is None:
            raise ValidationError(
                {
                    "success": False,
                    'message': "Email yoki telefon raqami kiritilishi shart!"
                }
            )
        user = User.objects.filter(Q(phone_number=email_or_phone) | Q(email=email_or_phone))
        if not user.exists():
            raise NotFound(detail="User not found")
        attrs['user'] = user.first()
        return attrs


class ResetPasswordSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    password = serializers.CharField(min_length=8, required=True, write_only=True)
    confirm_password = serializers.CharField(min_length=8, required=True, write_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'password',
            'confirm_password'
        )

    def validate(self, data):
        password = data.get('password', None)
        confirm_password = data.get('password', None)
        if password != confirm_password:
            raise ValidationError(
                {
                    'success': False,
                    'message': "Parollaringiz qiymati bir-biriga teng emas"
                }
            )
        if password:
            validate_password(password)
        return data

    def update(self, instance, validated_data):
        password = validated_data.pop('password')
        instance.set_password(password)
        return super(ResetPasswordSerializer, self).update(instance, validated_data)