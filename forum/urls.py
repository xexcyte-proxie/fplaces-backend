from rest_framework.routers import DefaultRouter

from forum.views import (
    CategoryViewSet,
    CommentViewSet,
    FloorViewSet,
    InterestViewSet,
    LocationConversationViewSet,
    PostViewSet,
    SectionViewSet,
    VenueViewSet,
)

app_name = "forum"

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("interests", InterestViewSet, basename="interest")
router.register("venues", VenueViewSet, basename="venue")
router.register("floors", FloorViewSet, basename="floor")
router.register("sections", SectionViewSet, basename="section")
router.register("posts", PostViewSet, basename="post")
router.register("comments", CommentViewSet, basename="comment")
router.register(
    "conversations", LocationConversationViewSet, basename="location-message"
)

urlpatterns = router.urls
