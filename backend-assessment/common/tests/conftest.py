import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def owner(db):
    return User.objects.create_user(
        email="owner@example.com", password="ownerpass", role="OWNER"
    )


@pytest.fixture
def participant(db):
    return User.objects.create_user(
        email="part@example.com", password="partpass", role="PARTICIPANT"
    )


@pytest.fixture
def owner_api(api, owner):
    resp = api.post(
        "/token/", {"email": owner.email, "password": "ownerpass"}, format="json"
    )
    assert resp.status_code == 200, resp.content
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return api


@pytest.fixture
def participant_api(api, participant):
    response = api.post(
        "/token/", {"email": participant.email, "password": "partpass"}, format="json"
    )
    assert response.status_code == 200, response.content
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return api
