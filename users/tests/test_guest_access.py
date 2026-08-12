import pytest
from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from users.models import GuestSession
from unittest.mock import patch

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def mock_mappedin():
    with patch("users.views.guest.fetch_mappedin_token") as mock:
        mock.return_value = {"token": "fake-mappedin-token"}
        yield mock

@pytest.mark.django_db
def test_create_guest_session_success(api_client, mock_mappedin):
    url = reverse("users:guest-access")
    payload = {
        "device_fingerprint": "test-device-123",
        "ip_address": "127.0.0.1",
    }
    
    response = api_client.post(url, data=payload, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access" in data
    assert data["token_type"] == "guest"
    assert data["has_tried_ar_view"] is False
    assert data["has_tried_2d_view"] is False
    assert data["trial_started_at"] is None
    assert data["trial_expires_at"] is None
    
    # Verify DB
    session = GuestSession.objects.get(device_fingerprint="test-device-123")
    assert session.ip_address == "127.0.0.1"
    assert session.has_tried_2d_view is False
    assert session.trial_started_at is None
    assert session.is_trial_active is True

@pytest.mark.django_db
def test_update_guest_session_starts_trial(api_client, mock_mappedin, settings):
    settings.GUEST_TRIAL_PERIOD_DAYS = 1
    
    # 1. Create session
    url = reverse("users:guest-access")
    payload = {
        "device_fingerprint": "test-device-456",
        "ip_address": "127.0.0.1",
    }
    response = api_client.post(url, data=payload, format="json")
    token = response.json()["access"]
    
    # 2. Update has_tried_2d_view to True
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    update_url = reverse("users:guest-update")
    
    update_response = api_client.patch(update_url, data={"has_tried_2d_view": True}, format="json")
    assert update_response.status_code == status.HTTP_200_OK
    assert update_response.json()["has_tried_2d_view"] is True
    assert update_response.json()["trial_started_at"] is not None
    
    # Verify DB trial started
    session = GuestSession.objects.get(device_fingerprint="test-device-456")
    assert session.has_tried_2d_view is True
    assert session.trial_started_at is not None
    assert session.is_trial_active is True
    
    # Verify expiration is exactly 1 day ahead
    expected_expiration = session.trial_started_at + timedelta(days=1)
    assert session.trial_expires_at == expected_expiration

@pytest.mark.django_db
def test_guest_session_expires_after_trial_period(api_client, mock_mappedin, settings):
    settings.GUEST_TRIAL_PERIOD_DAYS = 1
    
    # Create an expired session directly in DB
    past_time = timezone.now() - timedelta(days=2)
    session = GuestSession.objects.create(
        device_fingerprint="expired-device",
        ip_address="127.0.0.1",
        has_tried_2d_view=True,
        trial_started_at=past_time
    )
    
    # Attempt to login again with same fingerprint
    url = reverse("users:guest-access")
    payload = {
        "device_fingerprint": "expired-device",
        "ip_address": "127.0.0.1",
    }
    response = api_client.post(url, data=payload, format="json")
    
    # Should return 403 Forbidden
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "expired" in response.json()["detail"].lower()

@pytest.mark.django_db
def test_update_guest_session_invalid_token(api_client):
    url = reverse("users:guest-update")
    api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid-token")
    
    response = api_client.patch(url, data={"has_tried_2d_view": True}, format="json")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
