from rest_framework import serializers
from forum.models import Post
from users.serializers import PublicUserSerializer


class AdminPostSerializer(serializers.ModelSerializer):
    user = PublicUserSerializer(read_only=True)
    venue_name = serializers.CharField(source="venue.name", read_only=True)
    section_name = serializers.CharField(source="section.name", read_only=True, default=None)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "user",
            "venue",
            "venue_name",
            "section",
            "section_name",
            "category",
            "category_name",
            "content",
            "upvotes_count",
            "flags_count",
            "status",
            "is_archived",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "upvotes_count", "flags_count", "created_at", "updated_at"]
