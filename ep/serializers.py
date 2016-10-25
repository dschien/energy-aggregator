from rest_framework import serializers

from ep.models import Node, DeviceParameter, Site, Tariff, Band, TariffBandProperty, Gateway, \
    Device


class DeviceStateMeasurementSerializer(serializers.BaseSerializer):
    def to_representation(self, obj):
        # If you don't have a json serializable object
        # you can do the transformations here
        return obj


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ('name', 'id')


class GatewaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Gateway
        fields = ('external_id', 'id')


class NodeSerializer(serializers.ModelSerializer):
    """
    Used by the EBE
    """
    site = serializers.CharField(source='site.name', read_only=True)

    class Meta:
        model = Node
        fields = ('id', 'site')
        depth = 0


class NestedDeviceParameterSerializer(serializers.ModelSerializer):
    # site = serializers.CharField(source='device.node.site.name', read_only=True)
    type_name = serializers.CharField(source='type.code', read_only=True)

    class Meta:
        model = DeviceParameter
        fields = ('id', 'type', 'type_name')
        depth = 0


class DeviceSerializer(serializers.ModelSerializer):
    """
    Used by the EBE
    """
    site_name = serializers.CharField(source='node.gateway.site.name', read_only=True)
    site_id = serializers.CharField(source='node.gateway.site.id', read_only=True)
    gateway = serializers.CharField(source='node.gateway.id', read_only=True)
    node = serializers.CharField(source='node.id', read_only=True)
    type_name = serializers.CharField(source='type.code', read_only=True)
    device_parameters = NestedDeviceParameterSerializer(source='parameters', read_only=True, many=True)

    class Meta:
        model = Device
        fields = (
            'id', 'type_name', 'name', 'type', 'site_name', 'site_id', 'gateway', 'node', 'device_parameters',
            'precedence')
        depth = 0


class DeviceParameterSerializer(serializers.ModelSerializer):
    site = serializers.CharField(source='device.node.site.name', read_only=True)

    class Meta:
        model = DeviceParameter
        fields = ('id', 'site')
        depth = 0


class TariffBandPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = TariffBandProperty
        fields = ('key', 'value')


class BandSerializer(serializers.ModelSerializer):
    properties = TariffBandPropertySerializer(many=True, read_only=True)

    class Meta:
        model = Band
        fields = ('valid_from', 'valid_to', 'weekdays', 'start_time', 'end_time', 'properties')


class TariffSerializer(serializers.ModelSerializer):
    bands = BandSerializer(many=True, read_only=True)

    class Meta:
        model = Tariff
