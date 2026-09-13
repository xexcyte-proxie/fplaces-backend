from core.serializers import BaseSerializer
from forum.models import SectionMessage
from users.serializers import PublicUserSerializer


class SectionMessageSerializer(BaseSerializer):
    user = PublicUserSerializer(read_only=True)

    class Meta:
        model = SectionMessage
        fields = ["id", "section", "user", "content", "created_at", "updated_at"]
        read_only_fields = ["id", "user"]
        extra_kwargs = {
            "section": {"help_text": "The section this message belongs to. Each section has its own conversation thread."},
            "content": {"help_text": "Message text, max 500 characters."},
        }
