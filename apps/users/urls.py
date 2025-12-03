from django.urls import path
from .views import SignUpView, VerifyCodeView, UserInfoView, UserPhotoView, NewVerifyCodeView

app_name = 'users'

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('verify/', VerifyCodeView.as_view(), name='verify_code'),
    path('new-verify/', NewVerifyCodeView.as_view(), name='new_verify_code'),
    path('change-info/', UserInfoView.as_view(), name='change_info'),
    path('change-photo/', UserPhotoView.as_view(), name='change_photo'),
]