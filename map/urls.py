from django.urls import path
from .views import get_mappedin_token

urlpatterns = [
    path('api/maps/token/', get_mappedin_token, name='mappedin-token'),
]
