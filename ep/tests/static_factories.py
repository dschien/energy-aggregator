import datetime

import factory
from django.utils import timezone
from factory.fuzzy import FuzzyDateTime, FuzzyDecimal

from ep.models import Site, Vendor, Gateway, Node, DeviceType, Device, DeviceParameterType, DeviceParameter
from ep.tests.test_standalone import test_site, node_count


class SiteFactory(factory.django.DjangoModelFactory):
    """
    A factory that creates a new device with 10 measurements
    """

    class Meta:
        model = Site

    name = test_site

    @factory.post_generation
    def create_docs(self, create, extracted, **kwargs):
        if not create:
            return

        GatewayFactory.create(site=self, vendor=VendorFactory.create())


class VendorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Vendor

    name = "test_vendor"


class GatewayFactory(factory.django.DjangoModelFactory):
    """
    A factory that creates a new device with 10 measurements
    """

    class Meta:
        model = Gateway

    external_id = test_site

    @factory.post_generation
    def create_docs(self, create, extracted, **kwargs):
        if not create:
            return

        for i in range(0, node_count):
            NodeFactory.create(gateway=self)


class NodeFactory(factory.django.DjangoModelFactory):
    """
    A factory that creates a new device with 10 measurements
    """

    class Meta:
        model = Node

    vendor = VendorFactory.create(name="test_vendor")
    space_name = factory.Faker('name')
    external_id = factory.Sequence(lambda n: n)

    @factory.post_generation
    def create_docs(self, create, extracted, **kwargs):
        if not create:
            return

        DeviceFactory.create(node=self, type=DeviceTypeFactory.create(), vendor=VendorFactory.create())


factory_devices = []


class DeviceTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DeviceType

    code = "test_device"
    description = "This is a device for testing"


class DeviceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Device

    @factory.post_generation
    def create_docs(self, create, extracted, **kwargs):
        if not create:
            return

        device_param = DeviceParameterFactory.create(device=self, type=DeviceParameterTypeFactory.create())
        factory_devices.append(device_param.id)


class DeviceParameterTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DeviceParameterType

    code = "test_dp"
    description = "This is a device parameter for testing"


class DeviceParameterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DeviceParameter

    unit = 'units'

    @factory.post_generation
    def create_docs(self, create, extracted, **kwargs):
        if not create:
            return
        for i in range(0, 3):
            measurement_time = FuzzyDateTime(timezone.now() - datetime.timedelta(hours=1)).fuzz()
            value = FuzzyDecimal(0, 3).fuzz()
            self.measurements.add(time=measurement_time, value=value)
