from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import mixins, permissions, serializers, status, viewsets
from rest_framework.response import Response

from notifications.models import Notification
from notifications.serializers.admin import AdminNotificationRequestSerializer
from notifications.services.mail import send_template_email
from notifications.services.notify import notify

User = get_user_model()
_TAGS = ["Admin"]


@extend_schema_view(
    create=extend_schema(
        tags=_TAGS,
        summary="Broadcast an admin notification to targeted users",
        description=(
            "Sends an email, an in-app push (a `Notification` row with "
            "`verb=broadcast`, delivered live over `ws/notifications/`), or both, to "
            "active users matched by **any** of `venue`/`section`/`category` (users "
            "who have posted there) or explicit `users` ids — a union, not an "
            "intersection. At least one filter is required.\n\n"
            "Delivery is best-effort per user/channel: a failure sending to one user "
            "(e.g. a bad email address) is swallowed and doesn't stop the rest of the "
            "broadcast; the response reports how many sends actually succeeded via "
            "`email_sent`/`push_sent` versus how many users were matched "
            "(`users_targeted`)."
        ),
        request=AdminNotificationRequestSerializer,
        responses={
            201: inline_serializer(
                name="AdminNotificationResponse",
                fields={
                    "detail": serializers.CharField(),
                    "users_targeted": serializers.IntegerField(),
                    "email_sent": serializers.IntegerField(),
                    "push_sent": serializers.IntegerField(),
                },
            )
        },
    )
)
class AdminNotificationViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = AdminNotificationRequestSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        subject = data["subject"]
        message = data["message"]
        channels = data["channels"]

        venue_id = data.get("venue")
        section_id = data.get("section")
        category_id = data.get("category")
        user_ids = data.get("users")

        # Build query to target active users matching the union of specified filters
        q_filters = Q()
        if venue_id:
            q_filters |= Q(posts__venue_id=venue_id)
        if section_id:
            q_filters |= Q(posts__section_id=section_id)
        if category_id:
            q_filters |= Q(posts__category_id=category_id)
        if user_ids:
            q_filters |= Q(id__in=user_ids)

        users_to_notify = User.objects.filter(is_active=True).filter(q_filters).distinct()

        users_targeted = users_to_notify.count()
        email_sent = 0
        push_sent = 0

        for user in users_to_notify:
            if "email" in channels:
                try:
                    send_template_email(
                        to=user.email,
                        subject=subject,
                        template_name="admin_notification.html",
                        context={"subject": subject, "message": message},
                        text=message,
                    )
                    email_sent += 1
                except Exception:
                    # Log failure but continue processing other channels and users
                    pass

            if "push" in channels:
                try:
                    notify(
                        recipient=user,
                        verb=Notification.VERB_BROADCAST,
                        message=message,
                    )
                    push_sent += 1
                except Exception:
                    pass

        return Response(
            {
                "detail": "Admin notification broadcast completed.",
                "users_targeted": users_targeted,
                "email_sent": email_sent,
                "push_sent": push_sent,
            },
            status=status.HTTP_201_CREATED,
        )
