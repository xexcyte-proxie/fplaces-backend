import requests
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .services.mappedin import fetch_mappedin_token

from drf_spectacular.utils import extend_schema

@extend_schema(tags=["Maps"])
@api_view(['GET'])
@permission_classes([IsAuthenticated]) # Keep this endpoint secure!
def get_mappedin_token(request):
    try:
        data = fetch_mappedin_token()
        return JsonResponse(data)
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": "Failed to retrieve map token"}, status=500)
