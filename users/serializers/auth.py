from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import DjangoUnicodeDecodeError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from users.models import EmailVerificationOTP
from users.serializers.profile import UserSerializer
from users.tokens import email_verification_token
from users.utils import decode_uid

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        help_text="Must pass Django's password validators (min length 8, not too common, "
        "not too similar to your email).",
    )
    password_confirm = serializers.CharField(
        write_only=True, help_text="Must exactly match `password`."
    )

    class Meta:
        model = User
        fields = ["email", "password", "password_confirm"]
        extra_kwargs = {
            "email": {"help_text": "Used as the login identifier. Must be unique."},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            user_type=User.UserType.REGULAR_USER,
        )


class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(
        help_text="The email address of the account to verify."
    )
    otp = serializers.CharField(
        max_length=6,
        min_length=6,
        help_text="The 6-digit One-Time Password sent to your email."
    )

    def validate(self, attrs):
        email = attrs["email"]
        otp = attrs["otp"]

        try:
            user = User.all_objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "User with this email does not exist."})

        if user.is_email_verified:
            raise serializers.ValidationError({"email": "Email is already verified."})

        try:
            otp_instance = user.verification_otp
        except EmailVerificationOTP.DoesNotExist:
            raise serializers.ValidationError({"otp": "Invalid or expired OTP."})

        if not otp_instance.is_valid() or otp_instance.otp_code != otp:
            raise serializers.ValidationError({"otp": "Invalid or expired OTP."})

        attrs["user"] = user
        attrs["otp_instance"] = otp_instance
        return attrs


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(
        help_text="Account email to resend a verification OTP to. Always returns 200 "
        "whether or not the account exists, to avoid leaking which emails are registered."
    )


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(
        help_text="Account email to send a password reset link to. Always returns 200 "
        "whether or not the account exists, to avoid leaking which emails are registered."
    )


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(
        help_text="Base64url-encoded user id, taken from the `uid` query param in the "
        "password reset link sent by email."
    )
    token = serializers.CharField(
        help_text="Reset token from the `token` query param in the password reset link."
    )
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        help_text="Must pass Django's password validators.",
    )

    def validate(self, attrs):
        try:
            user_id = decode_uid(attrs["uid"])
            user = User.all_objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError, DjangoUnicodeDecodeError):
            raise serializers.ValidationError("Invalid reset link.")

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError("Invalid or expired reset link.")

        attrs["user"] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True, help_text="The account's current password, for re-authentication."
    )
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        help_text="Must pass Django's password validators.",
    )

    def validate_old_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(
        help_text="The refresh token issued at login, to be blacklisted so it can no "
        "longer be used to obtain new access tokens."
    )


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.USERNAME_FIELD

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
