from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class RootViewTests(APITestCase):
    def test_root_view_returns_ok_and_content(self):
        url = reverse("root")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"fPlaces is live", response.content)
