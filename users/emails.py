from django.conf import settings
from django.contrib.auth.tokens import default_token_generator

from notifications.services.mail import send_template_email
from users.models import EmailVerificationOTP
from users.utils import encode_uid


def send_verification_email(user):
    otp_instance = EmailVerificationOTP.generate_otp_for_user(user)
    otp_code = otp_instance.otp_code

    send_template_email(
        to=user.email,
        subject="Verify your email",
        template_name="verify_email.html",
        context={"otp_code": otp_code},
        text=(
            f"Welcome to {settings.PROJECT_NAME}!\n\n"
            f"Your verification code is: {otp_code}\n\n"
            f"Please enter this code in the app to verify your email address. "
            f"This code will expire in 15 minutes."
        ),
    )


def send_password_reset_email(user):
    uid = encode_uid(user.pk)
    token = default_token_generator.make_token(user)
    reset_url = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"

    send_template_email(
        to=user.email,
        subject="Reset your password",
        template_name="password_reset.html",
        context={"reset_url": reset_url},
        text=(
            f"You requested a password reset for your {settings.PROJECT_NAME} account.\n\n"
            f"Visit the link below to set a new password:\n{reset_url}\n\n"
            f"uid={uid}\ntoken={token}\n\n"
            "If you did not request this, you can safely ignore this email."
        ),
    )


def send_welcome_email(user):
    send_template_email(
        to=user.email,
        subject=f"Welcome to {settings.PROJECT_NAME}!",
        template_name="welcome.html",
        context={"frontend_url": settings.FRONTEND_URL, "user": user},
        text=(
            f"Welcome to {settings.PROJECT_NAME}!\n\n"
            f"Hi {user.pseudo_name or user.first_name or 'there'},\n\n"
            f"Your email has been successfully verified! We're thrilled to have you join our community.\n\n"
            f"Visit {settings.FRONTEND_URL} to get started, choose your pseudo name, and join a live feed!"
        ),
    )
