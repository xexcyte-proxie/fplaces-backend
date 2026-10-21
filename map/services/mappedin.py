import io
import json
import zipfile

import requests
from django.conf import settings
from loguru import logger

MAPPEDIN_API_BASE = "https://app.mappedin.com/api/v1"


def fetch_mappedin_token():
    url = f"{MAPPEDIN_API_BASE}/api-key/token"

    payload = {"key": settings.MAPPEDIN_KEY, "secret": settings.MAPPEDIN_SECRET}

    # Hit Mappedin's authentication endpoint
    response = requests.post(url, json=payload, timeout=10)

    if not response.ok:
        logger.error(f"[Mappedin Error] Status {response.status_code}: {response.text}")

    response.raise_for_status()

    data = response.json()

    return {"token": data.get("access_token"), "expires_in": data.get("expires_in")}


def _fetch_venue_details(venue_id, token):
    """Returns the raw venue object (with name/longitude/latitude/etc) from Mappedin's venue
    list endpoint, or None if not found. There's no GET /venue/{id} endpoint — only a list —
    so this pages through it looking for a matching id. limit=1000 (the API's max) covers any
    workspace short of an unrealistically large one; not worth paginating further for that.
    """
    response = requests.get(
        f"{MAPPEDIN_API_BASE}/venue",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": 1000, "include_archived": "true"},
        timeout=15,
    )
    response.raise_for_status()
    for venue in response.json().get("results", []):
        if venue.get("id") == venue_id:
            return venue
    return None


def fetch_venue_mappedin_data(venue_id):
    """Fetches a venue's data from Mappedin and returns:
    {
        "venue": <raw venue object or None>,
        "floors": [
            {
                "mappedin_floor_id", "name", "elevation", "order", "raw_json",
                "sections": [{"mappedin_location_id", "name", "raw_json"}],
            },
            ...
        ],
    }

    Mappedin's REST API has no direct "list floors"/"list sections" endpoint — floor and space
    data only exists inside the MVF zip returned by GET /venue/{id}/mvf. Within it:
      - map.geojson (despite the name, a plain JSON array, not GeoJSON) is the floor list; each
        floor is internally one Mappedin "map".
      - location.json holds the named, user-facing places ("sections" here) as Locations, each
        referencing one or more raw `space` geometry ids — but with no floor id of its own.
      - space/<floorId>.geojson holds each floor's raw space geometry.
    A Location is matched to its floor by intersecting its space ids against each floor's space
    id set. Only Locations with a name AND at least one space count as a "section" — this filters
    out bare point markers (e.g. plain entrances with no footprint).
    """
    token = fetch_mappedin_token()["token"]

    venue_raw = _fetch_venue_details(venue_id, token)

    mvf_response = requests.get(
        f"{MAPPEDIN_API_BASE}/venue/{venue_id}/mvf",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    mvf_response.raise_for_status()
    download_url = mvf_response.json()["url"]

    zip_response = requests.get(download_url, timeout=30)
    zip_response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(zip_response.content)) as archive:
        floors_raw = json.loads(archive.read("map.geojson"))
        locations_raw = json.loads(archive.read("location.json"))

        floor_space_ids = {}
        for floor in floors_raw:
            floor_id = floor["id"]
            try:
                space_data = json.loads(archive.read(f"space/{floor_id}.geojson"))
            except KeyError:
                space_data = {"features": []}
            floor_space_ids[floor_id] = {
                feature["properties"]["id"]
                for feature in space_data.get("features", [])
            }

    floors = []
    for order, floor in enumerate(floors_raw):
        floor_id = floor["id"]
        space_ids = floor_space_ids.get(floor_id, set())

        sections = []
        for location in locations_raw:
            name = location.get("name")
            location_space_ids = {space["id"] for space in location.get("spaces", [])}
            if name and location_space_ids and location_space_ids & space_ids:
                sections.append(
                    {
                        "mappedin_location_id": location["id"],
                        "name": name,
                        "raw_json": location,
                    }
                )

        floors.append(
            {
                "mappedin_floor_id": floor_id,
                "name": floor.get("name") or floor.get("externalId") or "",
                "elevation": floor.get("elevation"),
                "order": order,
                "raw_json": floor,
                "sections": sections,
            }
        )

    return {"venue": venue_raw, "floors": floors}
