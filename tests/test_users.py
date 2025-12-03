import pytest
from apps.users.models import User, UserConfirmation, AuthType, UserStatus
from unittest.mock import patch
from apps.users.serializers import SignUpSerializer, VerifiedCodeSerializer, InformationUserSerializer
from rest_framework.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

@pytest.mark.django_db
def test_signup_serializer_invalid_email():
    serializer = SignUpSerializer(data={"email_or_phone": "invalid"})
    with pytest.raises(ValidationError):
        serializer.is_valid(raise_exception=True)
    

@pytest.mark.django_db
def test_signup_serializer_valid_email():
    serializer = SignUpSerializer(data={"email_or_phone": "valid@example.com"})
    assert serializer.is_valid()
    assert serializer.context["auth_type"] == "email"

@pytest.mark.django_db
def test_signup_view(client):
    url = reverse("users:signup")
    payload = {"email_or_phone": "testuser@example.com"}
    response = client.post(url, payload, format="json")
    assert response.status_code == 200
    assert User.objects.filter(auth_type=AuthType.Email, email="testuser@example.com").exists()

@pytest.mark.django_db
def test_signup_existing_user(client):
    url = reverse("users:signup")
    payload = {"email_or_phone": "testuser@example.com"}
    response = client.post(url, payload, format="json")
    assert response.status_code == 200
    response = client.post(url, payload, format="json")
    assert response.status_code == 200
    assert User.objects.filter(auth_type=AuthType.Email, email="testuser@example.com").count() == 1


@pytest.mark.django_db
@patch("apps.users.tasks.send_verification_email.delay")
def test_signup_sends_email(mock_send_email, client):
    url = reverse("users:signup")
    payload = {"email_or_phone": "mockuser@example.com"}
    response = client.post(url, payload, format="json")
    assert response.status_code == 200
    mock_send_email.assert_called_once()

@pytest.mark.django_db
def test_verify_code_serializer_invalid_code():
    serializer = VerifiedCodeSerializer(data={"code": "wrongcode"})
    with pytest.raises(ValidationError):
        serializer.is_valid(raise_exception=True)

@pytest.mark.django_db
def test_verify_code_serializer_valid_code():
    serializer = VerifiedCodeSerializer(data={"code": "1234"})
    assert serializer.is_valid()

@pytest.mark.django_db
def test_verify_code_view(client):
    user = User.objects.create_user(email="user@example.com", auth_type=AuthType.Email, username="testuser")
    UserConfirmation.objects.create(user=user, code="1234", auth_type=AuthType.Email)
    url = reverse("users:verify_code")
    payload = {"code": "1234"}
    response = client.post(url, payload, format="json")
    assert response.status_code == 401

@pytest.mark.django_db
def test_verify_code_view_authenticated(authenticated_client, user):
    UserConfirmation.objects.create(user=user, code="1234", auth_type=AuthType.Email)
    url = reverse("users:verify_code")
    payload = {"code": "1234"}
    response = authenticated_client.post(url, payload, format="json")
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.user_status == UserStatus.CodeVerified
    assert user.username == "testuser"


@pytest.mark.django_db
def test_verify_code_view_invalid_code(authenticated_client, user):
    UserConfirmation.objects.create(user=user, code="1234", auth_type=AuthType.Email)
    url = reverse("users:verify_code")
    payload = {"code": "4321"}
    response = authenticated_client.post(url, payload, format="json")
    assert response.status_code == 400
    user.refresh_from_db()
    assert user.user_status == UserStatus.New

@pytest.mark.django_db
def test_verify_code_expired_time(authenticated_client, user):
    UserConfirmation.objects.create(user=user, code="1234", auth_type=AuthType.Email)
    url = reverse("users:verify_code")
    payload = {"code": "1234"}
    with patch("apps.users.views.timezone") as mock_timezone:
        mock_timezone.now.return_value = timezone.now() + timedelta(minutes=10)
        response = authenticated_client.post(url, payload, format="json")
    
    # проверяем, что код истёк
    assert response.status_code == 400  # или другой статус, который возвращает view
    user.refresh_from_db()
    assert user.user_status != UserStatus.CodeVerified


@pytest.mark.django_db
def test_new_verify_code_view(authenticated_client, user):
    url = reverse("users:new_verify_code")
    response = authenticated_client.post(url, format="json")
    assert response.status_code == 200
    assert UserConfirmation.objects.filter(user=user).exists()
    response2 = authenticated_client.post(url, format="json")
    assert response2.status_code == 400  # Уже есть действующий код 
    assert UserConfirmation.objects.filter(user=user).count() == 1

@pytest.mark.django_db
def test_new_verify_code_view_already_verified(authenticated_client, user):
    user.user_status = UserStatus.CodeVerified
    user.save()
    url = reverse("users:new_verify_code")
    response = authenticated_client.post(url, format="json")
    assert response.status_code == 400  # Пользователь уже проверен


@pytest.mark.django_db
def test_info_user_serializer(user):
    payload = {
        "username": "info_test_user",
        "first_name": "Info",
        "last_name": "User",
        "password": "StrongPassw0rd!",
        "confirm_password": "password!",  # ← правильный пароль
    }
    serializer = InformationUserSerializer(
        data=payload,
        context={'request_user': user}
    )
    assert not serializer.is_valid()



@pytest.mark.django_db
def test_info_user_serializer_username_taken(user):
    """Тест проверяет, что ошибка возникает при повторном использовании username"""
    # Создаём второго пользователя
    from apps.users.models import User as DjangoUser
    other_user = DjangoUser.objects.create_user(username="existing_user", password="pass123")
    
    payload = {
        "username": other_user.username,  # ← используем username другого пользователя
        "first_name": "Info",
        "last_name": "User",
        "password": "StrongPassw0rd!",
        "confirm_password": "StrongPassw0rd!",
    }
    serializer = InformationUserSerializer(
        data=payload,
        context={'request_user': user}  # ← контекст текущего пользователя
    )
    
    assert not serializer.is_valid()
    assert "Username is already taken." in str(serializer.errors)


@pytest.mark.django_db
def test_info_user_serializer_invalid_first_name(user):
    """Тест проверяет валидацию first_name (только буквы)"""
    payload = {
        "username": "new_test_user",
        "first_name": "Info123",  # ← содержит цифры
        "last_name": "User",
        "password": "StrongPassw0rd!",
        "confirm_password": "StrongPassw0rd!",
    }
    serializer = InformationUserSerializer(
        data=payload,
        context={'request_user': user}
    )
    
    assert not serializer.is_valid()
    assert "First name must contain only alphabetic characters." in str(serializer.errors)


@pytest.mark.django_db
def test_info_user_serializer_valid(user):
    """Тест проверяет успешную валидацию с корректными данными"""
    payload = {
        "username": "new_valid_user",
        "first_name": "John",
        "last_name": "Doe",
        "password": "StrongPassw0rd!",
        "confirm_password": "StrongPassw0rd!",
    }
    serializer = InformationUserSerializer(
        data=payload,
        context={'request_user': user}
    )
    
    assert serializer.is_valid()
    assert not serializer.errors
