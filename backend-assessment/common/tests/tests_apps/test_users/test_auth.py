import pytest
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db
User = get_user_model()


def test_jwt_obtain_and_refresh(client):
    user = User.objects.create_user(
        email="u@example.com", password="secret", role="OWNER"
    )
    response = client.post(
        "/token/", {"email": user.email, "password": "secret"}, format="json"
    )
    assert response.status_code == 200
    assert "access" in response.data and "refresh" in response.data

    response2 = client.post(
        "/token/refresh/", {"refresh": response.data["refresh"]}, format="json"
    )
    assert response2.status_code == 200
    assert "access" in response2.data
