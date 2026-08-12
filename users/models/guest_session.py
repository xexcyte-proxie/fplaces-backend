from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class GuestSession(models.Model):
    """
    Tracks a guest device's trial window.

    Uniqueness is keyed on `device_fingerprint` alone so that a VPN / IP
    change does not reset the trial clock.
    """

    device_fingerprint = models.CharField(
        max_length=512,
        unique=True,
        db_index=True,
        help_text="Opaque client-generated fingerprint that identifies this device.",
    )
    ip_address = models.GenericIPAddressField(
        help_text="Most-recent IP address seen for this guest.",
    )
    has_tried_ar_view = models.BooleanField(
        default=False,
        help_text="Whether the guest has tried the AR view feature.",
    )
    has_tried_2d_view = models.BooleanField(
        default=False,
        help_text="Whether the guest has tried the 2D view feature.",
    )
    trial_started_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-trial_started_at"]
        verbose_name = "Guest Session"
        verbose_name_plural = "Guest Sessions"

    def __str__(self):
        return f"Guest {self.device_fingerprint[:12]}… (started {self.trial_started_at:%Y-%m-%d %H:%M})"

    # ------------------------------------------------------------------
    # Trial helpers
    # ------------------------------------------------------------------

    @property
    def trial_expires_at(self):
        hours = getattr(settings, "GUEST_TRIAL_PERIOD_HOURS", 24)
        return self.trial_started_at + timedelta(hours=hours)

    @property
    def is_trial_active(self):
        return timezone.now() < self.trial_expires_at
