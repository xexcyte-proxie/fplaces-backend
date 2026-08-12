from rest_framework import serializers


class GuestAccessSerializer(serializers.Serializer):
    ip_address = serializers.IPAddressField(
        help_text="The guest's current IP address."
    )
    device_fingerprint = serializers.CharField(
        max_length=512,
        help_text=(
            "An opaque, client-generated string that uniquely identifies this "
            "device (e.g. a hash of browser/hardware attributes). "
            "The same fingerprint across requests ties activity to one trial window."
        ),
    )

class GuestSessionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        from users.models import GuestSession
        model = GuestSession
        fields = ["has_tried_ar_view", "has_tried_2d_view"]
