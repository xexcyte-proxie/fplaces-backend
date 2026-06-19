from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from core.serializers import DetailResponseSerializer
from users.emails import send_password_reset_email, send_verification_email
from users.serializers import (
    EmailTokenObtainPairSerializer,
    EmailVerificationSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    UserSerializer,
)

User = get_user_model()


@extend_schema_view(
    post=extend_schema(
        tags=["Auth"],
        summary="Register a new account",
        description=(
            "Creates a new user with `email` + `password` and immediately sends a "
            "verification email (see `POST /api/users/verify-email/`).\n\n"
            "The account is created with `is_email_verified=False` and no `pseudo_name`. "
            "Per the onboarding flow, the client should prompt the user to verify their "
            "email and then set a `pseudo_name` via `PATCH /api/users/me/` before letting "
            "them select a venue and post."
        ),
        request=RegisterSerializer,
        responses={201: UserSerializer, 400: DetailResponseSerializer},
        examples=[
            OpenApiExample(
                "Register request",
                value={
                    "email": "fan@example.com",
                    "password": "SuperSecret123!",
                    "password_confirm": "SuperSecret123!",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Register response",
                value={
                    "id": 1,
                    "email": "fan@example.com",
                    "pseudo_name": None,
                    "is_email_verified": False,
                    "created_at": "2026-06-19T00:04:56.813191Z",
                    "updated_at": "2026-06-19T00:04:56.813210Z",
                },
                response_only=True,
                status_codes=["201"],
            ),
        ],
    )
)
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_verification_email(user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    post=extend_schema(
        tags=["Auth"],
        summary="Log in and obtain a JWT pair",
        description=(
            "Authenticates with `email` + `password` and returns an `access` token "
            "(send as `Authorization: Bearer <access>` on subsequent requests, expires "
            "after 30 minutes) and a `refresh` token (expires after 14 days, used with "
            "`POST /api/users/token/refresh/` to obtain a new access token, or "
            "`POST /api/users/logout/` to invalidate it).\n\n"
            "The response also embeds the authenticated user's profile under `user`, "
            "so the client doesn't need a separate `GET /api/users/me/` call right after login."
        ),
        examples=[
            OpenApiExample(
                "Login request",
                value={"email": "fan@example.com", "password": "SuperSecret123!"},
                request_only=True,
            ),
            OpenApiExample(
                "Login response",
                value={
                    "refresh": "eyJhbGciOiJIUzI1NiIs...",
                    "access": "eyJhbGciOiJIUzI1NiIs...",
                    "user": {
                        "id": 1,
                        "email": "fan@example.com",
                        "pseudo_name": "BlueSeat42",
                        "is_email_verified": True,
                        "created_at": "2026-06-19T00:04:56.813191Z",
                        "updated_at": "2026-06-19T00:06:23.240753Z",
                    },
                },
                response_only=True,
            ),
        ],
    )
)
class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


@extend_schema_view(
    post=extend_schema(
        tags=["Auth"],
        summary="Verify an email address",
        description=(
            "Confirms the `email`/`otp` sent on "
            "registration (or resent via `POST /api/users/resend-verification/`), and "
            "sets `is_email_verified=True` on the matching account."
        ),
        request=EmailVerificationSerializer,
        responses={200: UserSerializer, 400: DetailResponseSerializer},
    )
)
class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        user.is_email_verified = True
        user.save(update_fields=["is_email_verified", "updated_at"])

        from users.emails import send_welcome_email
        send_welcome_email(user)

        otp_instance = serializer.validated_data.get("otp_instance")
        if otp_instance:
            otp_instance.delete()

        return Response(UserSerializer(user).data)


@extend_schema_view(
    post=extend_schema(
        tags=["Auth"],
        summary="Resend the verification email",
        description=(
            "Re-sends the verification email for an account that hasn't verified yet. "
            "Always returns `200` with a generic message, regardless of whether the "
            "email exists or is already verified, to avoid leaking account existence."
        ),
        request=ResendVerificationSerializer,
        responses={200: DetailResponseSerializer},
    )
)
class ResendVerificationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.all_objects.filter(
            email__iexact=serializer.validated_data["email"], is_email_verified=False
        ).first()
        if user:
            send_verification_email(user)
        return Response({"detail": "If that account exists, a verification email has been sent."})


@extend_schema_view(
    post=extend_schema(
        tags=["Auth"],
        summary="Request a password reset email",
        description=(
            "Sends a password reset email containing a `uid`/`token` pair to be "
            "submitted to `POST /api/users/password-reset-confirm/`. Always returns "
            "`200` with a generic message, regardless of whether the email exists, to "
            "avoid leaking account existence."
        ),
        request=PasswordResetRequestSerializer,
        responses={200: DetailResponseSerializer},
    )
)
class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.all_objects.filter(email__iexact=serializer.validated_data["email"]).first()
        if user:
            send_password_reset_email(user)
        return Response({"detail": "If that account exists, a password reset email has been sent."})


@extend_schema_view(
    post=extend_schema(
        tags=["Auth"],
        summary="Confirm a password reset",
        description=(
            "Completes a password reset using the `uid`/`token` pair from the reset "
            "email, setting `new_password` on the account. The token is single-use and "
            "expires per Django's `PASSWORD_RESET_TIMEOUT` (default 3 days)."
        ),
        request=PasswordResetConfirmSerializer,
        responses={200: DetailResponseSerializer, 400: DetailResponseSerializer},
    )
)
class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])
        return Response({"detail": "Password has been reset successfully."})


@extend_schema_view(
    post=extend_schema(
        tags=["Auth"],
        summary="Log out (blacklist refresh token)",
        description=(
            "Blacklists the given `refresh` token so it can no longer be used to "
            "obtain new access tokens. The current `access` token remains valid until "
            "it naturally expires (up to 30 minutes) since access tokens aren't tracked "
            "server-side; clients should discard it locally on logout."
        ),
        request=LogoutSerializer,
        responses={205: None, 400: DetailResponseSerializer},
    )
)
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_205_RESET_CONTENT)
