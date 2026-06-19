import random
from datetime import timedelta
from django.db import models
from django.utils import timezone
from core.models import BaseModel


class EmailVerificationOTP(BaseModel):
    user = models.OneToOneField(
        "users.User",
        on_delete=models.CASCADE,
        related_name="verification_otp",
    )
    otp_code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = "Email Verification OTP"
        verbose_name_plural = "Email Verification OTPs"

    def __str__(self):
        return f"{self.user.email} - {self.otp_code}"

    @classmethod
    def generate_otp_for_user(cls, user):
        otp_code = f"{random.randint(100000, 999999)}"
        expires_at = timezone.now() + timedelta(minutes=15)
        otp_instance, created = cls.objects.update_or_create(
            user=user,
            defaults={"otp_code": otp_code, "expires_at": expires_at, "is_archived": False},
        )
        return otp_instance

    def is_valid(self):
        return self.expires_at > timezone.now()
