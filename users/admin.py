from django.contrib import admin

from users.models import EmailVerificationOTP, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        "email",
        "pseudo_name",
        "is_email_verified",
        "is_staff",
        "is_active",
        "is_archived",
        "created_at",
    ]
    list_filter = ["is_staff", "is_active", "is_email_verified", "is_archived"]
    search_fields = ["email", "pseudo_name"]
    ordering = ["-created_at"]
    readonly_fields = ["password", "last_login", "created_at", "updated_at"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("pseudo_name",)}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_email_verified",
                    "is_archived",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (None, {"fields": ("email", "pseudo_name", "is_staff", "is_superuser")}),
    )
    filter_horizontal = ["groups", "user_permissions"]

    def get_queryset(self, request):
        return User.all_objects.all()

    def get_fieldsets(self, request, obj=None):
        return self.add_fieldsets if obj is None else self.fieldsets

    def save_model(self, request, obj, form, change):
        if not change:
            obj.set_unusable_password()
        super().save_model(request, obj, form, change)


@admin.register(EmailVerificationOTP)
class EmailVerificationOTPAdmin(admin.ModelAdmin):
    list_display = ["user", "otp_code", "expires_at", "is_valid_otp", "created_at"]
    list_filter = ["expires_at"]
    search_fields = ["user__email", "otp_code"]
    readonly_fields = ["created_at", "updated_at"]

    def is_valid_otp(self, obj):
        return obj.is_valid()
    is_valid_otp.boolean = True
    is_valid_otp.short_description = "Is Valid (Not Expired)"

    def get_queryset(self, request):
        return EmailVerificationOTP.all_objects.all()

