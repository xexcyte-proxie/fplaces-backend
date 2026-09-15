import requests
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .services.mappedin import fetch_mappedin_token

from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers


@extend_schema(
    tags=["Maps"],
    summary="Get a Mappedin map token",
    description="Returns a short-lived Mappedin access token used to render the venue's "
    "interactive 2D/AR map. Authenticated users only — guests instead receive an "
    "equivalent token bundled directly into their `POST /api/users/guest/` response.",
    responses={
        200: inline_serializer(
            name="MappedinTokenResponse",
            fields={
                "token": serializers.CharField(),
                "expires_in": serializers.IntegerField(),
            },
        ),
        500: OpenApiResponse(
            description="Failed to retrieve a token from the Mappedin API."
        ),
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])  # Keep this endpoint secure!
def get_mappedin_token(request):
    try:
        data = fetch_mappedin_token()
        return JsonResponse(data)
    except requests.exceptions.RequestException:
        return JsonResponse({"error": "Failed to retrieve map token"}, status=500)
