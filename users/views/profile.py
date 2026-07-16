from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from core.serializers import DetailResponseSerializer
from users.serializers import ChangePasswordSerializer, UserSerializer


@extend_schema_view(
    get=extend_schema(
        tags=["Users"],
        summary="Get the current user's profile",
        description="Returns the authenticated user's own profile, identified from the JWT.",
    ),
    put=extend_schema(
        tags=["Users"],
        summary="Replace the current user's profile",
        description="Full update of the authenticated user's profile. In practice only "
        "`pseudo_name` is writable; `email` and `is_email_verified` are read-only.",
    ),
    patch=extend_schema(
        tags=["Users"],
        summary="Update the current user's profile",
        description="Partial update of the authenticated user's profile — typically "
        "used to set `pseudo_name` during onboarding, after email verification.",
    ),
    delete=extend_schema(
        tags=["Users"],
        summary="Delete the current user's account",
        description="Permanently deletes the authenticated user's account and all associated data.",
    ),
)
class MeView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def perform_destroy(self, instance):
        instance.archive()


@extend_schema_view(
    post=extend_schema(
        tags=["Users"],
        summary="Change the current user's password",
        description="Changes the authenticated user's password, requiring the current "
        "`old_password` for re-authentication. Unlike the reset-password flow, this "
        "doesn't require an email round-trip since the user is already logged in.",
        request=ChangePasswordSerializer,
        responses={200: DetailResponseSerializer, 400: DetailResponseSerializer},
    )
)
class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password", "updated_at"])
        return Response({"detail": "Password changed successfully."})
