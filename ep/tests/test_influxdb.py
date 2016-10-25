import datetime
import time
import unittest
from _pydecimal import Decimal
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from influxdb import InfluxDBClient

from ep.models import DPMeasurements, DeviceParameter, Gateway, GCSMeasurements, DeviceParameterType
from ep.tests.static_factories import SiteFactory
from ep_secure_importer.controllers.secure_client import secure_site_name, SecureClient

if __name__ == '__main__':
    unittest.main()


class DPMeasurementTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiteFactory.create(name=secure_site_name)

    def test_simple_add(self):
        m = DPMeasurements(device_parameter=DeviceParameter.objects.first())
        before = len(list(m.all()))
        m.add(time=timezone.now(), value=255)
        m.add(time=timezone.now(), value=0)
        m.add(time=timezone.now(), value=20.5)
        time.sleep(1.5)
        after = len(list(m.all()))
        self.assertTrue(before + 3 == after)

    def test_latest(self):
        """
        """
        first = DeviceParameter.objects.all().first()
        measurements = first.measurements
        latest = measurements.latest()
        self.assertTrue(type(latest['value']) == Decimal)
        # chose a value that is different to the latest
        v = latest['value'] + Decimal('1.')
        measurements.add(parse_datetime(latest['time']) + datetime.timedelta(days=0, seconds=3), value=v)
        time.sleep(1.5)
        self.assertTrue(measurements.latest()['value'] == v)


class EmptyDBTestCase(TestCase):
    v = 10.
    client = InfluxDBClient(settings.INFLUXDB_HOST, settings.INFLUXDB_PORT, settings.INFLUXDB_USER,
                            settings.INFLUXDB_PASSWORD, settings.INFLUX_DB_NAME)

    def setUp(self):
        """
        Clear the DB before each test
        """
        INFLUX_DB_NAME = 'test_device_parameters'
        EmptyDBTestCase.client.create_database(INFLUX_DB_NAME)
        EmptyDBTestCase.client.drop_database(INFLUX_DB_NAME)
        EmptyDBTestCase.client.create_database(INFLUX_DB_NAME)

    def test_simple_DPMeasurements_add(self):
        t = DeviceParameterType(code="TEST")
        m = DPMeasurements(device_parameter=type('test_device_param', (object,),
                                                 {'id': 1, 'type': t, 'device': MagicMock()})())

        m.add(time=timezone.now(), value=EmptyDBTestCase.v)
        time.sleep(2.5)
        measurements = list(m.all())
        self.assertTrue(measurements[0]['value'] == EmptyDBTestCase.v)

    def test_simple_DPMeasurements_add_2(self):
        t = DeviceParameterType(code="TEST")
        m = DPMeasurements(device_parameter=type('test_device_param', (object,),
                                                 {'id': 1, 'type': t, 'device': MagicMock()})())

        m.add(time=timezone.now(), value=EmptyDBTestCase.v + 1)
        time.sleep(2.5)
        m.add(time=timezone.now(), value=EmptyDBTestCase.v)
        time.sleep(2.5)
        measurements = list(m.all())
        self.assertTrue(measurements[0]['value'] == EmptyDBTestCase.v)

    def test_parse_latest_TS(self):
        m = DPMeasurements(device_parameter=type('test_device_param', (object,),
                                                 {'id': 1, 'type': MagicMock(), 'device': MagicMock()})())

        m.add(time=timezone.now(), value=EmptyDBTestCase.v + 1)
        time.sleep(2.5)

        latest = m.latest()
        ts = parse_datetime(latest['time'])

        now = timezone.now()
        assert ts < now

    def test_simple_DPMeasurements_exists(self):
        m = DPMeasurements(device_parameter=type('test_device_param', (object,),
                                                 {'id': 1, 'type': MagicMock(), 'device': MagicMock()})())

        m.add(time=timezone.now(), value=EmptyDBTestCase.v)
        time.sleep(3)
        self.assertTrue(m.exists())

    def test_simple_DPMeasurements_exists_not(self):
        m = DPMeasurements(device_parameter=type('test_device_param', (object,),
                                                 {'id': 1, 'type': MagicMock(), 'device': MagicMock()})())
        self.assertTrue(not m.exists())

    def test_simple_DPMeasurements_count(self):
        m = DPMeasurements(device_parameter=type('test_device_param', (object,),
                                                 {'id': 1, 'type': MagicMock(), 'device': MagicMock()})())

        m.add(time=timezone.now(), value=EmptyDBTestCase.v)

        self.assertTrue(m.count() == 1)

    def test_simple_DPMeasurements_all_start_date(self):
        m = DPMeasurements(device_parameter=type('test_device_param', (object,),
                                                 {'id': 1, 'type': MagicMock(), 'device': MagicMock()})())

        now = timezone.now()
        for i in range(0, 60):
            m.add(time=now - datetime.timedelta(seconds=i), value=EmptyDBTestCase.v)
        time.sleep(2.5)
        self.assertTrue(m.count() == 60)

        res = m.all(start_date=now - datetime.timedelta(seconds=30))
        size = len(list(res))
        # print(size)
        self.assertTrue(abs(size - 30) < 2)

    @patch('amqpstorm.basic.Basic.publish')
    def test_DPMeasurements_notify_listeners(self, receiver):
        """
        Trigger "latest value changed signal" and call the signal receiver
        """

        m = DPMeasurements(device_parameter=type('test_device_param', (object,),
                                                 {'id': 1, 'type': MagicMock(), 'device': MagicMock()})())

        m.add(time=timezone.now(), value=EmptyDBTestCase.v)
        time.sleep(2.5)
        m.add(time=timezone.now(), value=EmptyDBTestCase.v + 1)
        self.assertEqual(receiver.call_count, 1)
        self.assertEqual(receiver.call_args[1]['exchange'], settings.IODICUS_MESSAGING_EXCHANGE_NAME)

    @patch('amqpstorm.basic.Basic.publish')
    def test_DPMeasurements_exists_notify_listeners(self, mock):
        """
        Trigger "latest value changed signal" while patching out the signal receiver
        """
        m = DPMeasurements(device_parameter=type('test_device_param', (object,),
                                                 {'id': 1, 'type': MagicMock(), 'device': MagicMock()})())

        m.add(time=timezone.now(), value=EmptyDBTestCase.v)
        time.sleep(2.5)
        m.add(time=timezone.now(), value=EmptyDBTestCase.v + 1)
        self.assertEqual(mock.call_count, 1)


class GCSMeasurementTestCase(TestCase):
    def test_simple_add(self):
        gateway = Gateway()
        gateway.external_id = '123456789'
        m = GCSMeasurements(gateway)
        before = len(list(m.all()))
        m.add(timezone.now(), True)
        m.add(timezone.now(), False)
        m.add(timezone.now(), True)
        time.sleep(1.5)
        after = len(list(m.all()))
        self.assertTrue(before + 3 == after)
