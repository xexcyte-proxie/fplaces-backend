import requests
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from map.services.mappedin import fetch_mappedin_token
from users.models import GuestSession
from users.serializers.guest import GuestAccessSerializer


class GuestAccessView(APIView):
    """
    Issue a short-lived guest JWT and MappedIn keys in a single round-trip.

    The trial window is tracked per device fingerprint and is valid for the 
    calendar day of first usage. Once the day expires, the client receives 
    a `403` and should prompt the user to create a full account.
    """

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Auth"],
        summary="Obtain a guest access token",
        description=(
            "Accepts an `ip_address` and `device_fingerprint` and returns a "
            "short-lived guest JWT (lifetime controlled by `GUEST_TOKEN_EXPIRATION_MINUTES`, "
            "default 60 min) together with the MappedIn API keys needed to render the map.\n\n"
            "The guest trial window is valid for the **same calendar day** of the first call "
            "for a given `device_fingerprint`. Subsequent calls on the same day re-issue a "
            "fresh JWT. If accessed on a subsequent day, the server returns `403`.\n\n"
            "The returned `access` token can be used as `Authorization: Bearer <token>` "
            "on any endpoint that accepts `IsAuthenticatedOrGuest` permission. "
            "The token carries `token_type=guest` in its payload."
        ),
        request=GuestAccessSerializer,
        responses={
            200: OpenApiResponse(
                description="Guest token and MappedIn credentials issued.",
                response=inline_serializer(
                    name="GuestAccessResponse",
                    fields={
                        "access": serializers.CharField(),
                        "token_type": serializers.CharField(),
                        "expires_in": serializers.IntegerField(),
                        "trial_expires_at": serializers.DateTimeField(),
                        "has_tried_ar_view": serializers.BooleanField(),
                        "has_tried_2d_view": serializers.BooleanField(),
                        "has_2d_trial_expired": serializers.BooleanField(),
                        "mappedin": inline_serializer(
                            name="GuestMappedInData",
                            fields={
                                "token": serializers.CharField(),
                                "expires_in": serializers.IntegerField(),
                            },
                        ),
                    },
                ),
            ),
            403: OpenApiResponse(description="Guest trial period has expired."),
            400: OpenApiResponse(description="Validation error."),
            502: OpenApiResponse(description="Failed to retrieve MappedIn token."),
        },
        examples=[
            OpenApiExample(
                "Guest access request",
                value={
                    "ip_address": "1.2.3.4",
                    "device_fingerprint": "fp_abc123xyz",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Guest access response",
                value={
                    "access": "eyJhbGciOiJIUzI1NiIs...",
                    "token_type": "guest",
                    "expires_in": 3600,
                    "trial_expires_at": "2026-08-11T21:17:00Z",
                    "has_tried_ar_view": False,
                    "has_tried_2d_view": False,
                    "has_2d_trial_expired": False,
                    "mappedin": {
                        "token": "<mappedin-access-token>",
                        "expires_in": 3600,
                    },
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def post(self, request):
        serializer = GuestAccessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        device_fingerprint = serializer.validated_data["device_fingerprint"]
        ip_address = serializer.validated_data["ip_address"]

        # ----------------------------------------------------------------
        # 1. Get or create the guest session
        # ----------------------------------------------------------------
        guest_session, _ = GuestSession.objects.get_or_create(
            device_fingerprint=device_fingerprint,
            defaults={"ip_address": ip_address},
        )

        # Always keep ip_address current (the fingerprint is the unique key)
        if guest_session.ip_address != ip_address:
            guest_session.ip_address = ip_address
            guest_session.save(update_fields=["ip_address", "last_seen_at"])

        # ----------------------------------------------------------------
        # 2. Enforce the trial window
        # ----------------------------------------------------------------
        if not guest_session.is_trial_active:
            return Response(
                {"detail": "Guest trial period has expired. Please register to continue."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # ----------------------------------------------------------------
        # 3. Issue a short-lived guest JWT
        # ----------------------------------------------------------------
        expiration_minutes = getattr(settings, "GUEST_TOKEN_EXPIRATION", timedelta(minutes=60))
        if isinstance(expiration_minutes, timedelta):
            expiration = expiration_minutes
        else:
            expiration = timedelta(minutes=int(expiration_minutes))

        token = AccessToken()
        token.set_exp(lifetime=expiration)
        token["token_type"] = "guest"
        token["sub"] = f"guest:{device_fingerprint}"
        token["device_fingerprint"] = device_fingerprint

        expires_in_seconds = int(expiration.total_seconds())

        # ----------------------------------------------------------------
        # 4. Fetch MappedIn credentials
        # ----------------------------------------------------------------
        try:
            mappedin_data = fetch_mappedin_token()
        except requests.exceptions.RequestException:
            return Response(
                {"detail": "Failed to retrieve MappedIn token. Please try again later."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {
                "access": str(token),
                "token_type": "guest",
                "expires_in": expires_in_seconds,
                "trial_started_at": guest_session.trial_started_at,
                "trial_expires_at": guest_session.trial_expires_at,
                "has_tried_ar_view": guest_session.has_tried_ar_view,
                "has_tried_2d_view": guest_session.has_tried_2d_view,
                "has_2d_trial_expired": guest_session.has_2d_trial_expired,
                "mappedin": mappedin_data,
            },
            status=status.HTTP_200_OK,
        )


class GuestSessionUpdateView(APIView):
    """
    Get or update guest session fields like has_tried_ar_view or has_tried_2d_view.
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def _get_guest_session(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            raise serializers.ValidationError({"detail": "Authentication credentials were not provided."})
            
        token_string = auth_header.split(' ')[1]
        try:
            from rest_framework_simplejwt.tokens import UntypedToken
            token = UntypedToken(token_string)
        except Exception:
            raise serializers.ValidationError({"detail": "Invalid or expired token."})
            
        if token.get('token_type') != 'guest':
            raise serializers.ValidationError({"detail": "Not a valid guest token."})
            
        device_fingerprint = token.get('device_fingerprint')
        if not device_fingerprint:
            raise serializers.ValidationError({"detail": "Guest token missing device fingerprint."})
            
        try:
            return GuestSession.objects.get(device_fingerprint=device_fingerprint)
        except GuestSession.DoesNotExist:
            raise serializers.ValidationError({"detail": "Guest session not found."})

    @extend_schema(
        tags=["Auth"],
        summary="Get guest session preferences",
        responses={200: inline_serializer(
            name="GuestSessionResponse",
            fields={
                "has_tried_ar_view": serializers.BooleanField(),
                "has_tried_2d_view": serializers.BooleanField(),
                "has_2d_trial_expired": serializers.BooleanField(),
            },
        )}
    )
    def get(self, request):
        try:
            guest_session = self._get_guest_session(request)
        except serializers.ValidationError as e:
            # We can map some validation errors to 401/403/404 if desired, 
            # but returning 400 with the detail is also fine for a quick helper.
            # Let's do a simple mapping based on the message.
            detail = e.detail
            if isinstance(detail, dict) and "detail" in detail:
                msg = detail["detail"]
                if "credentials" in msg or "Invalid" in msg:
                    return Response(detail, status=status.HTTP_401_UNAUTHORIZED)
                if "Not a valid" in msg:
                    return Response(detail, status=status.HTTP_403_FORBIDDEN)
                if "not found" in msg:
                    return Response(detail, status=status.HTTP_404_NOT_FOUND)
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        from users.serializers.guest import GuestSessionUpdateSerializer
        serializer = GuestSessionUpdateSerializer(guest_session)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Auth"],
        summary="Update guest session preferences",
        request=inline_serializer(
            name="GuestSessionUpdateRequest",
            fields={
                "has_tried_ar_view": serializers.BooleanField(required=False),
                "has_tried_2d_view": serializers.BooleanField(required=False),
            },
        ),
        responses={200: OpenApiResponse(description="Guest session updated successfully.")}
    )
    def patch(self, request):
        try:
            guest_session = self._get_guest_session(request)
        except serializers.ValidationError as e:
            detail = e.detail
            if isinstance(detail, dict) and "detail" in detail:
                msg = detail["detail"]
                if "credentials" in msg or "Invalid" in msg:
                    return Response(detail, status=status.HTTP_401_UNAUTHORIZED)
                if "Not a valid" in msg:
                    return Response(detail, status=status.HTTP_403_FORBIDDEN)
                if "not found" in msg:
                    return Response(detail, status=status.HTTP_404_NOT_FOUND)
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
            
        from users.serializers.guest import GuestSessionUpdateSerializer
        serializer = GuestSessionUpdateSerializer(guest_session, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_200_OK)
