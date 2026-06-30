import requests
from django.conf import settings

def fetch_mappedin_token():
    url = "https://app.mappedin.com/api/v1/api-key/token"
    
    payload = {
        "key": settings.MAPPEDIN_KEY,
        "secret": settings.MAPPEDIN_SECRET
    }
    
    # Hit Mappedin's authentication endpoint
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    
    return {
        "token": data.get("access_token"), 
        "expires_in": data.get("expires_in")
    }
