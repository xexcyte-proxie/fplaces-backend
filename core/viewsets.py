from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet


class BaseViewSet(ModelViewSet):
    ordering = ["-created_at"]
    filter_backends_ordering_fields = ["created_at", "updated_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(is_archived=False)

    def perform_destroy(self, instance):
        instance.archive()

    @extend_schema(
        summary="Restore from soft-delete",
        description="Un-archives a record previously removed via `DELETE`, setting "
        "`is_archived` back to `False` so it reappears in normal list/retrieve queries.",
        request=None,
    )
    @action(detail=True, methods=["post"])
    def restore(self, request, *args, **kwargs):
        instance = self.get_queryset().model.all_objects.get(pk=kwargs["pk"])
        instance.restore()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
