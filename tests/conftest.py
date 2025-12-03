import pytest
from rest_framework.test import APIClient
from apps.users.models import User

@pytest.fixture
def client():
    """DRF APIClient"""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Тестовый админ"""
    return User.objects.create_superuser(email="admin@example.com")

@pytest.fixture
def user(db):
    """Тестовый пользователь"""
    return User.objects.create_user(email="user@example.com", password="password", auth_type="email", username="testuser")

@pytest.fixture
def authenticated_client(client,user):
    """Клиент с JWT авторизацией"""
    from rest_framework_simplejwt.tokens import RefreshToken
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client
