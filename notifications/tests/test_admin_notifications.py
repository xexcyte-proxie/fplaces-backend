from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from forum.models import Category, Post, Section, Venue
from notifications.models import Notification

User = get_user_model()


class AdminNotificationTests(APITestCase):
    def setUp(self):
        # Create normal users
        self.user1 = User.objects.create_user(
            email="user1@example.com", password="Password123!"
        )
        self.user2 = User.objects.create_user(
            email="user2@example.com", password="Password123!"
        )
        self.user3 = User.objects.create_user(
            email="user3@example.com", password="Password123!"
        )

        # Create admin user
        self.admin_user = User.objects.create_user(
            email="admin@example.com", password="AdminPassword123!", is_staff=True
        )

        # Create forum structure
        self.venue1 = Venue.objects.create(name="Venue One", location="Location One")
        self.venue2 = Venue.objects.create(name="Venue Two", location="Location Two")

        self.section1 = Section.objects.create(venue=self.venue1, name="Section One")
        self.section2 = Section.objects.create(venue=self.venue2, name="Section Two")

        self.category1 = Category.objects.create(name="Category One")
        self.category2 = Category.objects.create(name="Category Two")

        # Create posts to establish associations
        # User 1 is active in Venue 1, Section 1, Category 1
        self.post1 = Post.objects.create(
            user=self.user1,
            venue=self.venue1,
            section=self.section1,
            category=self.category1,
            content="User 1 post content",
        )

        # User 2 is active in Venue 2, Section 2, Category 2
        self.post2 = Post.objects.create(
            user=self.user2,
            venue=self.venue2,
            section=self.section2,
            category=self.category2,
            content="User 2 post content",
        )

        # User 3 has no posts (isolated user)

        # URL for admin notifications endpoint
        self.broadcast_url = reverse("admin_api:notification-list")

    def test_anonymous_user_blocked(self):
        response = self.client.post(self.broadcast_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_normal_user_blocked(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.broadcast_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_requires_at_least_one_target_filter(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "subject": "Admin Update",
            "message": "Hello community",
            "channels": ["push"],
        }
        response = self.client.post(self.broadcast_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data["details"])
        self.assertEqual(
            response.data["details"]["non_field_errors"][0],
            "At least one target filter (venue, section, category, or users) must be provided.",
        )

    def test_admin_requires_basic_fields(self):
        self.client.force_authenticate(user=self.admin_user)
        # Empty payload
        response = self.client.post(self.broadcast_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("subject", response.data["details"])
        self.assertIn("message", response.data["details"])
        self.assertIn("channels", response.data["details"])

    @patch("notifications.views.admin.send_template_email")
    @patch("notifications.services.notify.broadcast")
    def test_filter_by_venue(self, mock_broadcast, mock_send_email):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "subject": "Venue One Alert",
            "message": "Specific venue message",
            "channels": ["push", "email"],
            "venue": self.venue1.id,
        }
        response = self.client.post(self.broadcast_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["users_targeted"], 1)
        self.assertEqual(response.data["email_sent"], 1)
        self.assertEqual(response.data["push_sent"], 1)

        # User 1 should have a Notification created
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.user1, verb=Notification.VERB_BROADCAST, message="Specific venue message"
            ).exists()
        )
        # User 2 and User 3 should not
        self.assertFalse(Notification.objects.filter(recipient=self.user2).exists())
        self.assertFalse(Notification.objects.filter(recipient=self.user3).exists())

        # Assert WebSocket broadcast was triggered for user 1
        mock_broadcast.assert_called_once()
        args = mock_broadcast.call_args[0]
        self.assertEqual(args[0], f"user_{self.user1.id}")
        self.assertEqual(args[1], "notification")

        # Assert email was sent
        mock_send_email.assert_called_once()
        email_kwargs = mock_send_email.call_args[1]
        self.assertEqual(email_kwargs["to"], self.user1.email)
        self.assertEqual(email_kwargs["subject"], "Venue One Alert")
        self.assertEqual(email_kwargs["template_name"], "admin_notification.html")

    @patch("notifications.views.admin.send_template_email")
    def test_filter_by_section(self, mock_send_email):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "subject": "Section Alert",
            "message": "Specific section message",
            "channels": ["email"],
            "section": self.section1.id,
        }
        response = self.client.post(self.broadcast_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["users_targeted"], 1)
        self.assertEqual(response.data["email_sent"], 1)

        # Check only user1 received
        mock_send_email.assert_called_once()
        self.assertEqual(mock_send_email.call_args[1]["to"], self.user1.email)

    @patch("notifications.views.admin.send_template_email")
    def test_filter_by_category(self, mock_send_email):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "subject": "Category Alert",
            "message": "Specific category message",
            "channels": ["email"],
            "category": self.category2.id,
        }
        response = self.client.post(self.broadcast_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["users_targeted"], 1)
        self.assertEqual(response.data["email_sent"], 1)

        # Check only user2 received (associated with category 2)
        mock_send_email.assert_called_once()
        self.assertEqual(mock_send_email.call_args[1]["to"], self.user2.email)

    @patch("notifications.views.admin.send_template_email")
    def test_filter_by_custom_users_list(self, mock_send_email):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "subject": "Direct Alert",
            "message": "Message for specific users",
            "channels": ["email"],
            "users": [self.user1.id, self.user3.id],
        }
        response = self.client.post(self.broadcast_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["users_targeted"], 2)
        self.assertEqual(response.data["email_sent"], 2)

        # Both user1 and user3 emails sent
        emails_sent_to = [call[1]["to"] for call in mock_send_email.call_args_list]
        self.assertIn(self.user1.email, emails_sent_to)
        self.assertIn(self.user3.email, emails_sent_to)
        self.assertNotIn(self.user2.email, emails_sent_to)

    @patch("notifications.views.admin.send_template_email")
    def test_union_prevents_duplicate_deliveries(self, mock_send_email):
        self.client.force_authenticate(user=self.admin_user)
        # Target user1 via both their venue (venue1) and custom users list
        payload = {
            "subject": "Union Alert",
            "message": "Message targeting multiple criteria",
            "channels": ["email"],
            "venue": self.venue1.id,
            "users": [self.user1.id, self.user2.id],
        }
        response = self.client.post(self.broadcast_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Should target user1 and user2 once each
        self.assertEqual(response.data["users_targeted"], 2)
        self.assertEqual(response.data["email_sent"], 2)

        emails_sent_to = [call[1]["to"] for call in mock_send_email.call_args_list]
        self.assertEqual(len(emails_sent_to), 2)
        self.assertIn(self.user1.email, emails_sent_to)
        self.assertIn(self.user2.email, emails_sent_to)
