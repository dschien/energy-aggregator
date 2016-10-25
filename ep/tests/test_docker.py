import unittest

import json

import time
from celery import current_app
from django.conf import settings
from django.utils import timezone

from ep.models import DPMeasurements, DeviceParameter

from ep.tasks import send_msg
from django.test import TestCase, modify_settings, override_settings

from ep.tests.static_factories import SiteFactory
from ep_secure_importer.controllers.secure_client import secure_site_name

__author__ = 'schien'


@override_settings(IODICUS_MESSAGING_HOST='messaging.iodicus.net')
class TaskTest(TestCase):
    def test_messaging(self):
        print(settings.IODICUS_MESSAGING_HOST)
        # print(settings.BROKER_URL)
        self.assertTrue(send_msg.delay(json.dumps({'test': 1})))

class LocalTaskTest(TestCase):
    def test_messaging(self):
        print(settings.IODICUS_MESSAGING_HOST)
        print(settings.BROKER_URL)
        self.assertTrue(send_msg.delay(json.dumps({'test': 1})))


# @override_settings(INFLUXDB_HOST='52.49.171.8')
class InfluxDBTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiteFactory.create(name=secure_site_name)

    # @unittest.skip
    def test_simple_add(self):
        print(settings.INFLUXDB_HOST)
        m = DPMeasurements(device_parameter=DeviceParameter.objects.first())
        before = len(list(m.all()))
        print(before)
        m.add(time=timezone.now(), value=255)
        m.add(time=timezone.now(), value=0)
        m.add(time=timezone.now(), value=20.5)
        time.sleep(5)
        after = len(list(m.all()))
        print(after)

        self.assertTrue(before + 3 == after)


if __name__ == '__main__':
    unittest.main()
