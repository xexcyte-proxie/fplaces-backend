from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import EmailVerificationOTP

User = get_user_model()


class EmailVerificationTests(APITestCase):
    def setUp(self):
        self.register_url = reverse("users:register")
        self.verify_url = reverse("users:verify-email")
        self.resend_url = reverse("users:resend-verification")
        self.user_data = {
            "email": "testuser@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
        }

    @patch("users.emails.send_template_email")
    def test_registration_generates_otp_and_sends_email(self, mock_send_email):
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email=self.user_data["email"])
        self.assertFalse(user.is_email_verified)

        # Check OTP generated
        otp_instance = EmailVerificationOTP.objects.get(user=user)
        self.assertEqual(len(otp_instance.otp_code), 6)
        self.assertTrue(otp_instance.is_valid())

        # Check email sent with OTP
        mock_send_email.assert_called_once()
        kwargs = mock_send_email.call_args[1]
        self.assertEqual(kwargs["to"], user.email)
        self.assertEqual(kwargs["context"]["otp_code"], otp_instance.otp_code)

    @patch("users.emails.send_template_email")
    def test_successful_otp_verification(self, mock_send_email):
        # Register user to generate OTP
        self.client.post(self.register_url, self.user_data)
        user = User.objects.get(email=self.user_data["email"])
        otp_instance = EmailVerificationOTP.objects.get(user=user)
        otp_code = otp_instance.otp_code

        # Verify
        verify_data = {"email": user.email, "otp": otp_code}
        response = self.client.post(self.verify_url, verify_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # User is verified
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)

        # OTP record is cleaned up/deleted
        self.assertFalse(EmailVerificationOTP.objects.filter(user=user).exists())

        # Assert welcome email is sent
        self.assertEqual(mock_send_email.call_count, 2)
        welcome_call = mock_send_email.call_args_list[1]
        kwargs = welcome_call[1]
        self.assertEqual(kwargs["to"], user.email)
        self.assertEqual(kwargs["template_name"], "welcome.html")
        self.assertEqual(kwargs["context"]["frontend_url"], "http://localhost:3000")


    @patch("users.emails.send_template_email")
    def test_failed_verification_invalid_otp(self, mock_send_email):
        # Register user
        self.client.post(self.register_url, self.user_data)
        user = User.objects.get(email=self.user_data["email"])
        otp_instance = EmailVerificationOTP.objects.get(user=user)

        # Verify with wrong OTP
        verify_data = {"email": user.email, "otp": "000000"}
        response = self.client.post(self.verify_url, verify_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("otp", response.data["details"])

        # User remains unverified
        user.refresh_from_db()
        self.assertFalse(user.is_email_verified)
        self.assertTrue(EmailVerificationOTP.objects.filter(user=user).exists())

    @patch("users.emails.send_template_email")
    def test_failed_verification_expired_otp(self, mock_send_email):
        # Register user
        self.client.post(self.register_url, self.user_data)
        user = User.objects.get(email=self.user_data["email"])
        otp_instance = EmailVerificationOTP.objects.get(user=user)

        # Force expire the OTP
        otp_instance.expires_at = timezone.now() - timedelta(seconds=1)
        otp_instance.save()

        # Verify
        verify_data = {"email": user.email, "otp": otp_instance.otp_code}
        response = self.client.post(self.verify_url, verify_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # User remains unverified
        user.refresh_from_db()
        self.assertFalse(user.is_email_verified)

    @patch("users.emails.send_template_email")
    def test_resend_verification_generates_new_otp(self, mock_send_email):
        # Register
        self.client.post(self.register_url, self.user_data)
        user = User.objects.get(email=self.user_data["email"])
        otp_instance1 = EmailVerificationOTP.objects.get(user=user)
        code1 = otp_instance1.otp_code

        # Reset mock
        mock_send_email.reset_mock()

        # Resend
        resend_data = {"email": user.email}
        response = self.client.post(self.resend_url, resend_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify new OTP created
        otp_instance2 = EmailVerificationOTP.objects.get(user=user)
        self.assertNotEqual(otp_instance1.otp_code, otp_instance2.otp_code)

        # Verify email sent
        mock_send_email.assert_called_once()
        kwargs = mock_send_email.call_args[1]
        self.assertEqual(kwargs["context"]["otp_code"], otp_instance2.otp_code)
