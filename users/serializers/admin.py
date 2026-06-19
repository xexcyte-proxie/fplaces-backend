from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "pseudo_name",
            "is_email_verified",
            "is_staff",
            "is_active",
            "is_archived",
            "created_at",
            "last_login",
        ]
        read_only_fields = ["created_at", "last_login"]


class CategoryStatSerializer(serializers.Serializer):
    category_name = serializers.CharField()
    post_count = serializers.IntegerField()


class VenueStatSerializer(serializers.Serializer):
    venue_name = serializers.CharField()
    post_count = serializers.IntegerField()


class AdminStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    verified_users = serializers.IntegerField()
    total_posts = serializers.IntegerField()
    total_comments = serializers.IntegerField()
    flagged_posts_count = serializers.IntegerField()
    active_venues_count = serializers.IntegerField()
    posts_by_category = CategoryStatSerializer(many=True)
    posts_by_venue = VenueStatSerializer(many=True)
