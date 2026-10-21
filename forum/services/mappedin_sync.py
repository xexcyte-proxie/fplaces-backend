from decimal import Decimal, InvalidOperation

from forum.models import Floor, Section, Venue


def _to_decimal(value):
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def sync_venue_from_mappedin(venue):
    """Pulls latitude/longitude/raw_json, floors, and sections for `venue` from Mappedin
    and writes them (via update_or_create, so repeat calls are idempotent). Shared by the
    Venue post_save signal, the `sync_mappedin` management command, and the admin "Sync
    from Mappedin" button, so all three stay in sync with one implementation.

    Raises on failure — callers decide how to handle it (the signal logs and swallows it,
    the management command reports and continues to the next venue, the admin view shows
    it as an error message).

    Returns {"floors_count", "sections_count", "venue_found"}.
    """
    if not venue.mappedin_map_id:
        raise ValueError("venue has no mappedin_map_id set")

    from map.services.mappedin import fetch_venue_mappedin_data

    data = fetch_venue_mappedin_data(venue.mappedin_map_id)

    venue_raw = data["venue"]
    if venue_raw:
        latitude = _to_decimal(venue_raw.get("latitude"))
        longitude = _to_decimal(venue_raw.get("longitude"))
        Venue.objects.filter(pk=venue.pk).update(
            latitude=latitude, longitude=longitude, raw_json=venue_raw
        )
        venue.latitude = latitude
        venue.longitude = longitude
        venue.raw_json = venue_raw

    sections_count = 0
    for floor_data in data["floors"]:
        floor, _ = Floor.objects.update_or_create(
            venue=venue,
            mappedin_floor_id=floor_data["mappedin_floor_id"],
            defaults={
                "name": floor_data["name"],
                "elevation": floor_data["elevation"],
                "order": floor_data["order"],
                "raw_json": floor_data["raw_json"],
            },
        )
        for section_data in floor_data["sections"]:
            Section.objects.update_or_create(
                floor=floor,
                mappedin_location_id=section_data["mappedin_location_id"],
                defaults={
                    "venue": venue,
                    "name": section_data["name"],
                    "raw_json": section_data["raw_json"],
                },
            )
            sections_count += 1

    return {
        "floors_count": len(data["floors"]),
        "sections_count": sections_count,
        "venue_found": venue_raw is not None,
    }
