import json
from decimal import Decimal
from unittest import skip
# from unittest.mock import patch
import unittest.mock as mock
from celery import current_app
from django.conf import settings
from django.test import TestCase

from ep.models import Site, ScheduleDeviceParameterGroup, DeviceParameter, StateChangeEvent
from ep.tasks import send_msg, scheduled_device_state_change
from ep.tests.static_factories import SiteFactory
from ep_secure_importer.controllers.secure_client import secure_site_name, SecureClient
from django.test import TestCase, modify_settings, override_settings
from prefect.tasks import import_from_site

__author__ = 'schien'


@override_settings(SECURE_SERVERS={'test-server': {'HOST': settings.TEST_SECURE_SERVER_HOST + ':8080',
                                                   'WSHOST': settings.TEST_SECURE_SERVER_HOST + ':5678',
                                                   'USER': "guest", 'PASSWORD': 'guest'}})
class TaskTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        settings.CELERY_ALWAYS_EAGER = True
        current_app.conf.CELERY_ALWAYS_EAGER = True

    # @skip('we can only run this on a fully deployed stack')
    def test_messaging(self):
        self.assertTrue(send_msg.delay(json.dumps({'test': 1})))

    @skip('we can only run this on a fully deployed stack')
    def test_import(self):
        Site(name='goldney').save()
        self.assertTrue(import_from_site.delay('goldney'))

    def test_schedule(self):
        inst = SecureClient('test-server')
        with mock.patch.object(inst, 'update_device_data',
                               wraps=inst.update_device_data) as update_device_data:
            # with patch('ep_secure_importer.controllers.secure_client.update_device_data') as update_device_data:
            update_device_data.return_value = ("server response", 200)

            SiteFactory.create(name=secure_site_name)
            first = DeviceParameter.objects.all().first()

            s = ScheduleDeviceParameterGroup()
            s.save()
            s.device_parameters.add(first)
            current_value = first.measurements.latest()['value']
            target_value = current_value + 1

            scheduled_device_state_change.delay(device_group_id=s.id, target_value=target_value)

            self.assertTrue(update_device_data.called)
            call_args = json.loads(update_device_data.call_args[0][0])
            cv = call_args['DeviceData']['DPDO'][0]['CV']
            self.assertTrue(target_value == Decimal(str(cv)))

    def test_trigger_source_heuristic(self):
        with mock.patch('pylibmc.Client') as mc:
            SiteFactory.create(name="test")
            dp = DeviceParameter.objects.all().first()

            SecureClient.store_device_state_change_request(dp.id, 1, StateChangeEvent.SCHEDULE)
            source = SecureClient.get_trigger_source(dp, 1)

            # @patch('ep.signals.device_parameter_state_change.send_robust')
            # @httpretty.activate
            # def test_detect_setpoint_change(self, mock):
            #     result = device_parameter_state_change.send_robust(sender=self.__class__, device_parameter_id=123,
            #                                                        type='test setting', previous='previous', new='new value',
            #                                                        trigger='test trigger')
            #     print(result)
            #     self.assertTrue(mock.called)
            #     self.assertTrue(mock.call_count == 1)
            #     self.assertTrue(mock.call_args_list[0][1]['trigger'] == 'test trigger')
