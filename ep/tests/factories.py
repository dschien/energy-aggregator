"""
Usage example:
    @patch('amqpstorm.Connection')
    def test_site_factory(self, mock):
        test_name = 'site factory test'
        site = SiteFactory(name=test_name, gateway__external_id=test_name, gateway__vendor__name=test_name)

        self.assertTrue(site.name == test_name)
        self.assertTrue(site.gateways.first().external_id == test_name)
        self.assertTrue(site.gateways.first().vendor.name == test_name)

"""
import random

import factory
from faker.factory import Factory as FakerFactory

from ep.models import Vendor, DeviceType, DeviceParameterType, DeviceParameter, Device, Node, Gateway, Site, Tariff

faker = FakerFactory.create()


class VendorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Vendor

    name = factory.LazyAttribute(lambda o: faker.company())


class DeviceTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DeviceType

    code = factory.LazyAttribute(lambda o: faker.lexify(text="????").upper())


class DefaultDeviceParameterActionsDeviceParameterFactory(object):
    pass


class DeviceParameterTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DeviceParameterType

    code = factory.LazyAttribute(lambda o: faker.lexify(text="????").upper())


class DeviceParameterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DeviceParameter

    type = factory.SubFactory(DeviceParameterTypeFactory)


class DeviceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Device

    vendor = factory.SubFactory(VendorFactory)
    type = factory.SubFactory(DeviceTypeFactory)
    device_param = factory.RelatedFactory(DeviceParameterFactory, 'device')


class NodeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Node

    # is created after this node instance
    vendor = factory.SubFactory(VendorFactory)
    device = factory.RelatedFactory(DeviceFactory, 'node', vendor=factory.SelfAttribute('node.vendor'))


class GatewayFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Gateway

    # min = 123456789, max = 99999999
    external_id = factory.LazyAttribute(lambda o: faker.random_int())

    # is created first
    node = factory.RelatedFactory(NodeFactory, 'gateway', vendor=factory.SelfAttribute('gateway.vendor'))
    vendor = factory.SubFactory(VendorFactory)


class SiteFactory(factory.django.DjangoModelFactory):
    """
    A factory that creates a new device with 10 measuremnts
    """

    class Meta:
        model = Site

    name = factory.LazyAttribute(lambda o: faker.street_name())
    gateway = factory.RelatedFactory(GatewayFactory, 'site')


class TariffFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tariff

    name = factory.LazyAttribute(lambda o: faker.street_name())
    enabled = factory.LazyAttribute(lambda o: bool(random.getrandbits(1)))
