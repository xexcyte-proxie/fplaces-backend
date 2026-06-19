from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from forum.models import Category, Comment, Post, PostFlag, Venue
from users.models import EmailVerificationOTP

User = get_user_model()


class AdminApiTests(APITestCase):
    def setUp(self):
        # Create normal user
        self.normal_user = User.objects.create_user(
            email="normal@example.com", password="NormalPassword123!"
        )

        # Create admin/staff user
        self.admin_user = User.objects.create_user(
            email="admin@example.com", password="AdminPassword123!", is_staff=True
        )

        # Create basic forum data for stats
        self.venue = Venue.objects.create(name="Starlight Arena", location="Main Street")
        self.category = Category.objects.create(name="Fan Vibe", description="All about the fans")
        self.post = Post.objects.create(
            user=self.normal_user,
            venue=self.venue,
            category=self.category,
            content="Testing the admin panel stats",
        )
        self.comment = Comment.objects.create(
            post=self.post, user=self.normal_user, content="Nice post!"
        )

        # URLs
        self.stats_url = reverse("admin_api:stats")
        self.users_list_url = reverse("admin_api:user-list")
        self.posts_list_url = reverse("admin_api:post-list")

    def test_anonymous_user_blocked_from_admin_endpoints(self):
        # Stats
        response = self.client.get(self.stats_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        # Users list
        response = self.client.get(self.users_list_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        # Posts list
        response = self.client.get(self.posts_list_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_normal_authenticated_user_blocked_from_admin_endpoints(self):
        self.client.force_authenticate(user=self.normal_user)

        # Stats
        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Users list
        response = self.client.get(self.users_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_stats_dashboard(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertEqual(data["total_users"], 2)
        self.assertEqual(data["total_posts"], 1)
        self.assertEqual(data["total_comments"], 1)
        self.assertEqual(data["active_venues_count"], 1)
        self.assertEqual(len(data["posts_by_category"]), 1)
        self.assertEqual(data["posts_by_category"][0]["category_name"], "Fan Vibe")
        self.assertEqual(data["posts_by_category"][0]["post_count"], 1)

    def test_admin_user_management(self):
        self.client.force_authenticate(user=self.admin_user)

        # List all users
        response = self.client.get(self.users_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

        # Archive user
        archive_url = reverse("admin_api:user-archive", kwargs={"pk": self.normal_user.pk})
        response = self.client.post(archive_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.normal_user.refresh_from_db()
        self.assertTrue(self.normal_user.is_archived)

        # Restore user
        restore_url = reverse("admin_api:user-restore", kwargs={"pk": self.normal_user.pk})
        response = self.client.post(restore_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.normal_user.refresh_from_db()
        self.assertFalse(self.normal_user.is_archived)

        # Toggle staff status
        toggle_staff_url = reverse("admin_api:user-toggle-staff", kwargs={"pk": self.normal_user.pk})
        response = self.client.post(toggle_staff_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.normal_user.refresh_from_db()
        self.assertTrue(self.normal_user.is_staff)

    def test_admin_post_moderation_actions(self):
        self.client.force_authenticate(user=self.admin_user)

        # Hide post
        hide_url = reverse("admin_api:post-hide", kwargs={"pk": self.post.pk})
        response = self.client.post(hide_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, Post.STATUS_HIDDEN)

        # Show post
        show_url = reverse("admin_api:post-show", kwargs={"pk": self.post.pk})
        response = self.client.post(show_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, Post.STATUS_VISIBLE)

        # Archive/soft-delete post
        response = self.client.delete(reverse("admin_api:post-detail", kwargs={"pk": self.post.pk}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.post.refresh_from_db()
        self.assertTrue(self.post.is_archived)

        # Restore post
        restore_url = reverse("admin_api:post-restore", kwargs={"pk": self.post.pk})
        response = self.client.post(restore_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertFalse(self.post.is_archived)

    def test_admin_moderation_flags_handling(self):
        self.client.force_authenticate(user=self.admin_user)

        # Add a flag to the post
        PostFlag.objects.create(post=self.post, user=self.normal_user, reason="Spam content")
        self.post.flags_count = 1
        self.post.save()

        # Check flagged posts list
        flagged_url = reverse("admin_api:post-flagged")
        response = self.client.get(flagged_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.post.id)

        # Clear flags
        clear_flags_url = reverse("admin_api:post-clear-flags", kwargs={"pk": self.post.pk})
        response = self.client.post(clear_flags_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.flags_count, 0)
        self.assertFalse(PostFlag.objects.filter(post=self.post, is_archived=False).exists())
