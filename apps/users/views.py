from django.utils import timezone
from rest_framework.views import APIView, Response, status
from .serializers import SignUpSerializer, VerifiedCodeSerializer, InformationUserSerializer, UserPhotoSerializer, \
    LoginSerializer, LoginRefreshSerializer, LogoutSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
from rest_framework import permissions 
from .models import AuthType, UserStatus, UserConfirmation, User, PHONE_TIME, EMAIL_TIME 

from django.core.exceptions import ObjectDoesNotExist




class SignUpView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            auth_type = serializer.context['auth_type']
            email_or_phone = serializer.validated_data['email_or_phone'].lower()
            if auth_type == AuthType.Email:
                user = User.objects.get_or_create(email=email_or_phone, auth_type=auth_type)[0]
            else:
                user = User.objects.get_or_create(phone_number=email_or_phone, auth_type=auth_type)[0]
            user.generate_code(auth_type)

            data = {
                "success": True,
                "access": user.token()['access'],
                "refresh": user.token()['refresh'],
                "user_status": user.user_status,
            }

            return Response(data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class VerifyCodeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = VerifiedCodeSerializer(data=request.data)
        if serializer.is_valid():
            code = serializer.validated_data['code']
            user = request.user
            try:
                confirmation = UserConfirmation.objects.get(user=user, code=code)
            except UserConfirmation.DoesNotExist:
                return Response({"success": False, "detail": "Invalid verification code."}, status=status.HTTP_400_BAD_REQUEST)
            if user.user_status != UserStatus.New:
                return Response({"success": False, "detail": "User is already verified."}, status=status.HTTP_400_BAD_REQUEST)
            if timezone.now() > confirmation.expired_time:
                return Response({"detail": "Code expired"}, status=status.HTTP_400_BAD_REQUEST)

            user.user_status = UserStatus.CodeVerified
            user.save()
            confirmation.delete()

            data = {
                "success": True,
                "access": user.token()['access'],
                "refresh": user.token()['refresh'],
                "user_status": user.user_status,
            }
            return Response(data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class NewVerifyCodeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.user_status != UserStatus.New:
            return Response({"success": False, "detail": "User is already verified."}, status=status.HTTP_400_BAD_REQUEST)
        if UserConfirmation.objects.filter(user=user, expired_time__gt=timezone.now()).exists():
            return Response({"success": False, "detail": "A valid verification code has already been sent."}, status=status.HTTP_400_BAD_REQUEST)
        user.generate_code(user.auth_type)
        return Response({"success": True, "detail": "A new verification code has been sent."}, status=status.HTTP_200_OK)


class UserInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        serializer = InformationUserSerializer(data=request.data, context={'request_user': request.user})
        if serializer.is_valid():
            user = request.user
            user.username = serializer.validated_data['username']
            user.first_name = serializer.validated_data['first_name']
            user.last_name = serializer.validated_data['last_name']
            user.set_password(serializer.validated_data['password'])
            user.user_status = UserStatus.Done
            user.save()

            data = {
                "success": True,
                "access": user.token()['access'],
                "refresh": user.token()['refresh'],
                "user_status": user.user_status,
            }
            return Response(data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserPhotoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        serializer = UserPhotoSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            photo = serializer.validated_data.get('photo')
            if photo:
                user.photo = photo
                user.user_status = UserStatus.Photo_Done
                user.save()
            data = {
                "success": True,
                "access": user.token()['access'],
                "refresh": user.token()['refresh'],
                "user_status": user.user_status,    
            }
            return Response(data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
