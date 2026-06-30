from datetime import timedelta
from django.db.models import Count
from django.utils import timezone

from core.realtime import broadcast, venue_group


def broadcast_venue_heatmap(venue_id):
    from forum.models import Post

    five_mins_ago = timezone.now() - timedelta(minutes=5)
    
    section_counts = Post.objects.filter(
        venue_id=venue_id,
        status=Post.STATUS_VISIBLE,
        created_at__gte=five_mins_ago,
        section__isnull=False
    ).values("section_id").annotate(post_count=Count("id")).order_by("-post_count")

    heatmap = []
    for entry in section_counts:
        count = entry["post_count"]
        
        if count >= 5:
            priority = "high"
        elif count >= 2:
            priority = "medium"
        else:
            priority = "low"
            
        heatmap.append({
            "section_id": entry["section_id"],
            "post_count": count,
            "priority": priority
        })

    broadcast(
        venue_group(venue_id),
        "section_heat_update",
        {"heatmap": heatmap}
    )
