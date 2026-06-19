from core.realtime import broadcast, user_group
from notifications.models import Notification
from notifications.serializers import NotificationSerializer


def notify(*, recipient, verb, actor=None, post=None, comment=None, message=""):
    if actor is not None and actor.pk == recipient.pk:
        return None

    notification = Notification.objects.create(
        recipient=recipient,
        actor=actor,
        verb=verb,
        post=post,
        comment=comment,
        message=message,
    )

    broadcast(user_group(recipient.id), "notification", NotificationSerializer(notification).data)
    return notification
