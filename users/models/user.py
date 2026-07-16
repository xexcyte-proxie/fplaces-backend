from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from core.models import BaseModel
from users.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    class UserType(models.TextChoices):
        REGULAR_USER = "regular_user", "Regular User"
        ADMIN = "admin", "Admin"

    email = models.EmailField(unique=True)
    pseudo_name = models.CharField(max_length=50, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)
    avatar_url = models.URLField(max_length=1024, blank=True, null=True)
    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.REGULAR_USER,
    )

    is_email_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    interests = models.JSONField(blank=True, null=True)

    objects = UserManager()
    all_objects = models.Manager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    @property
    def display_name(self):
        return self.pseudo_name or self.email.split("@")[0]

    def archive(self):
        super().archive()
        
        # GDPR / Privacy compliance: Anonymize personal identifiable information
        self.is_active = False
        self.first_name = ""
        self.last_name = ""
        self.bio = ""
        self.avatar_url = ""
        
        # Use pseudo_name and email safely without hitting max_length constraints
        self.pseudo_name = f"deleted_{self.id}"
        self.email = f"deleted_{self.id}@anonymized.local"
        
        self.save(update_fields=[
            "is_active", 
            "first_name", 
            "last_name", 
            "bio", 
            "avatar_url", 
            "pseudo_name", 
            "email"
        ])
