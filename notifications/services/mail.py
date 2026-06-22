import logging

import resend
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_template_email(*, to, subject, template_name, context, text):
    html = render_to_string(
        f"notifications/emails/{template_name}",
        {"project_name": settings.PROJECT_NAME, **context},
    )
    return send_email(to=to, subject=subject, text=text, html=html)


def send_email(*, to, subject, text, html=None):
    recipients = [to] if isinstance(to, str) else list(to)

    if not settings.RESEND_API_KEY:
        logger.info(
            "RESEND_API_KEY not set; logging email instead of sending.\nTo: %s\nSubject: %s\n\n%s",
            recipients,
            subject,
            text,
        )
        return None

    resend.api_key = settings.RESEND_API_KEY
    params = {
        "from": settings.DEFAULT_FROM_EMAIL,
        "to": recipients,
        "subject": subject,
        "text": text,
    }
    if html:
        params["html"] = html

    return resend.Emails.send(params)
