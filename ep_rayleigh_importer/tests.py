import logging
from unittest.mock import patch

from django.test import TestCase
from ep.models import Node, Device, DeviceParameter
import json

from .controllers.rayleigh_client import default_rayleigh_api_host, RayleighClient
from .data_tests import devices_data_resp, device_id, sensor_data_resp

__author__ = 'mitchell'
logger = logging.getLogger(__name__)

test_client_id = 'test_client'
test_app_id = 'test_app'
test_token = 'test_token'


def create_rayleigh_client():
    return RayleighClient(test_client_id, test_app_id, test_token, default_rayleigh_api_host)


class MockedImportRayleighTests(TestCase):
    @patch('ep_rayleigh_importer.controllers.rayleigh_client.requests')
    def import_devices(self, mock):
        """
        Helper Function: imports Rayleigh Connect devices into test database. Uses data from data_tests.py

        :param mock: A mock requests object for stubbing the API results
        """
        mock.get.return_value.status_code = 200
        mock.get.return_value.content = json.dumps(devices_data_resp)

        client = create_rayleigh_client()

        old_node_count = Node.objects.count()

        client.retrieve_devices()

        new_node_count = Node.objects.count()

        return old_node_count, new_node_count

    def test_import_devices(self):
        """
        Test: tests that the devices are imported correctly. Uses data from data_tests.py

        :param mock: A mock requests object for stubbing the API results
        """

        # The data, sensor_data_resp, contains one node (the name of which is stored in `data_tests.device_id`) to
        # import. This imports is tested by examining the difference in the number of entries stored in the db for this
        # model.

        old_node_count, new_node_count = self.import_devices()
        self.assertTrue(new_node_count == old_node_count + 1)

    @patch('ep_rayleigh_importer.controllers.rayleigh_client.DPMeasurements.add')
    @patch('ep_rayleigh_importer.controllers.rayleigh_client.requests')
    def test_import_sensors(self, mock, mock_ts):
        """
        Test: tests that the sensors are imported correctly. Requires test_import_devices to be run first.
        Uses data from data_tests.py

        :param mock: A mock requests object for stubbing the API results
        :param mock_ts: A mock DPMeasurements object to avoid populating the timeseries database
        """
        mock.get.return_value.status_code = 200
        mock.get.return_value.content = json.dumps(sensor_data_resp)

        self.import_devices()

        client = create_rayleigh_client()
        device_set = Node.objects.filter(external_id=device_id)
        if device_set.count() == 0:
            self.fail('Rayleigh Device (Node) was not found')
        device = device_set.get()

        device_count = Device.objects.count()
        device_parameter_count = DeviceParameter.objects.count()

        client.retrieve_sensors(device)

        new_device_count = Device.objects.count()
        new_device_parameter_count = DeviceParameter.objects.count()

        # The data, sensor_data_resp, contains one device (e1) and three relevant sensors (e1.kwh, e1.v3p and e1.i3p)
        # to import. These imports are tested by examining the difference in the number of entries stored in the db
        # for these models.

        kwh_device_parameter_count = 1
        v3p_device_parameter_count = 3
        i3p_device_parameter_count = 3

        self.assertTrue(new_device_count == device_count + 1)
        self.assertTrue(new_device_parameter_count ==
                        (device_parameter_count +
                         kwh_device_parameter_count +
                         v3p_device_parameter_count +
                         i3p_device_parameter_count)
                        )
