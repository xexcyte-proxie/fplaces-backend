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

    The trial window (`GUEST_TRIAL_PERIOD_HOURS`) is tracked per device
    fingerprint.  Once the window expires the client receives a `403` and
    should prompt the user to create a full account.
    """

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Auth"],
        summary="Obtain a guest access token",
        description=(
            "Accepts an `ip_address` and `device_fingerprint` and returns a "
            "short-lived guest JWT (lifetime controlled by `GUEST_TOKEN_EXPIRATION_MINUTES`, "
            "default 60 min) together with the MappedIn API keys needed to render the map.\n\n"
            "The guest trial window (`GUEST_TRIAL_PERIOD_HOURS`, default 24 h) is measured from "
            "the **first** call for a given `device_fingerprint`.  Subsequent calls within "
            "that window re-issue a fresh JWT without resetting the clock.  "
            "Once the window expires the server returns `403`.\n\n"
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
                "trial_expires_at": guest_session.trial_expires_at,
                "mappedin": mappedin_data,
            },
            status=status.HTTP_200_OK,
        )


class GuestSessionUpdateView(APIView):
    """
    Update guest session fields like has_tried_ar_view or has_tried_2d_view.
    """
    permission_classes = [permissions.AllowAny]

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
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return Response({"detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)
            
        token_string = auth_header.split(' ')[1]
        try:
            token = AccessToken(token_string)
        except Exception:
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_401_UNAUTHORIZED)
            
        if token.get('token_type') != 'guest':
            return Response({"detail": "Not a valid guest token."}, status=status.HTTP_403_FORBIDDEN)
            
        device_fingerprint = token.get('device_fingerprint')
        if not device_fingerprint:
            return Response({"detail": "Guest token missing device fingerprint."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            guest_session = GuestSession.objects.get(device_fingerprint=device_fingerprint)
        except GuestSession.DoesNotExist:
            return Response({"detail": "Guest session not found."}, status=status.HTTP_404_NOT_FOUND)
            
        from users.serializers.guest import GuestSessionUpdateSerializer
        serializer = GuestSessionUpdateSerializer(guest_session, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_200_OK)
