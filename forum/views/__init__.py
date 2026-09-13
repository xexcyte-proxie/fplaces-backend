from forum.views.category import CategoryViewSet
from forum.views.comment import CommentViewSet
from forum.views.interest import InterestViewSet
from forum.views.post import PostViewSet
from forum.views.section import SectionViewSet
from forum.views.section_message import SectionMessageViewSet
from forum.views.venue import VenueViewSet

__all__ = [
    "CategoryViewSet",
    "InterestViewSet",
    "VenueViewSet",
    "SectionViewSet",
    "PostViewSet",
    "CommentViewSet",
    "SectionMessageViewSet",
]
