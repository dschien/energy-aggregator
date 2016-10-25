import copy
import json
import logging
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import httpretty
from celery import current_app
from django.conf import settings
from django.test import TestCase


from ep.tests.factories import SiteFactory
from prefect.controllers.prefect import PrefectController, node_addresses_site_format_url, individual_node_status_url, \
    url_node_configuration_site_id_format_string, all_node_stati_url, badock_site_name

from ep.models import Node, Device, DeviceParameter, DeviceType, DeviceParameterType
from prefect.models import PrefectDeviceType, PrefectDeviceParameterType
from prefect.tasks import import_from_site

__author__ = 'schien'
logger = logging.getLogger(__name__)

current_time = datetime.now().timestamp()
basic_node_state = [{'Address': 3, "RoomName": "test_room", "ProgramName": "", "SetPointTemperature": 21.2,
                     "TemperatureAdjustment": 0, "CurrentTemperature": 12, 'L1On': False, 'L2On': True,
                     'AdjustedAtReceiver': True, 'LastReceiveAt': current_time, 'PresenceIsDetected': False}]

basic_node_state_6002 = [{'Address': 6002, "RoomName": "test_room", "ProgramName": "", "SetPointTemperature": 21.2,
                          "TemperatureAdjustment": 0, "CurrentTemperature": 12, 'L1On': False, 'L2On': True,
                          'AdjustedAtReceiver': True, 'LastReceiveAt': 1453727379, 'PresenceIsDetected': False}]

minimal_history = [{'Address': 3,
                    'History': [{'CurrentTemperature': 16.5,
                                 'L1On': False,
                                 'L2On': False,
                                 'ProgramName': 'Heating',
                                 'ReceivedAt': 1450051216,
                                 'SetPointTemperature': 14.0},
                                ]}]

actual_history = [{'Address': 3,
                   'History': [{'CurrentTemperature': 16.5,
                                'L1On': False,
                                'L2On': False,
                                'ProgramName': 'Corridor Heating',
                                'ReceivedAt': 1450051216,
                                'SetPointTemperature': 14.0},
                               {'CurrentTemperature': 16.5,
                                'L1On': False,
                                'L2On': False,
                                'ProgramName': 'Corridor Heating',
                                'ReceivedAt': 1450051442,
                                'SetPointTemperature': 14.0},
                               ]}]
badock_site = 'badock'

actual_node_config = [{'Address': 3,
                       'L1LoadWatts': 0,
                       'L2LoadWatts': 2000,
                       'RoomName': 'L Stairwell First'}]

actual_node_config_6002 = [{'Address': 6002,
                            'L1LoadWatts': 0,
                            'L2LoadWatts': 2000,
                            'RoomName': 'L Stairwell First'}]


class MockCeleryImportPrefectTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        settings.CELERY_ALWAYS_EAGER = True
        current_app.conf.CELERY_ALWAYS_EAGER = True

    @patch('amqpstorm.Connection')
    @httpretty.activate
    def test_import_all(self, connectionMock):
        node_ids = [190, 191, 192]
        "Mock for get status of all device method"
        httpretty.register_uri(httpretty.GET, all_node_stati_url.format(site=badock_site),
                               body=json.dumps(actual_node_statii),
                               content_type="application/json")

        httpretty.register_uri(httpretty.GET, node_addresses_site_format_url.format(site=badock_site),
                               body=json.dumps(node_ids),
                               content_type="application/json")

        for node_id in node_ids:
            formatted_url = individual_node_status_url.format(site=badock_site, id=node_id)

            state = copy.deepcopy(basic_node_state)
            state[0]['Address'] = node_id

            httpretty.register_uri(httpretty.GET, formatted_url,
                                   body=json.dumps(state),
                                   content_type="application/json")

            "Mock for get configuration method"
            httpretty.register_uri(httpretty.GET,
                                   url_node_configuration_site_id_format_string.format(site=badock_site, id=node_id),
                                   body=json.dumps(actual_node_config),
                                   content_type="application/json")

        # first = PrefectDevice.objects.all().first()

        import_from_site.delay(badock_site)
        # assert PrefectDevice.objects.count() == prior + 1

    @patch('amqpstorm.Connection')
    def test_site_factory(self, mock):
        test_name = 'site factory test'
        site = SiteFactory(name=test_name, gateway__external_id=test_name, gateway__vendor__name=test_name)

        self.assertTrue(site.name == test_name)
        self.assertTrue(site.gateways.first().external_id == test_name)
        self.assertTrue(site.gateways.first().vendor.name == test_name)
        print(site.gateways.first().nodes.first())

    @patch('amqpstorm.Connection')
    @patch('ep.controllers.secure_client.requests')
    def test_import_single(self, req_mock, conn_mock):
        name = 'test_site'
        SiteFactory(name=name)

        formatted_url = individual_node_status_url.format(site=name.upper(), id=6002)

        req_mock.get.side_effect = lambda k: 'pass'

        # httpretty.register_uri(httpretty.GET, formatted_url,
        #                        body=json.dumps(basic_node_state_6002),
        #                        content_type="application/json")
        #
        # "Mock for get configuration method"
        # httpretty.register_uri(httpretty.GET,
        #                        url_node_configuration_site_id_format_string.format(site=test_site, id=6002),
        #                        body=json.dumps(actual_node_config),
        #                        content_type="application/json")

        import_from_site.delay(name, 6002)
        # assert PrefectDevice.objects.count() == prior + 1


daysAgo = 1


def set_up_http_mocks():
    """
    Mock for get_node_ids method
    :return:
    """

    httpretty.register_uri(httpretty.GET, node_addresses_site_format_url.format(site=badock_site.upper()),
                           body=json.dumps([1, 2, 3]),
                           content_type="application/json")

    "Mock for get status of individual device method"
    httpretty.register_uri(httpretty.GET, individual_node_status_url.format(site=badock_site.upper(), id=3),
                           body=json.dumps(basic_node_state),
                           content_type="application/json")

    "Mock for get status of all device method"
    httpretty.register_uri(httpretty.GET, all_node_stati_url.format(site=badock_site.upper()),
                           body=json.dumps(actual_node_statii),
                           content_type="application/json")

    "Mock for get configuration method"
    httpretty.register_uri(httpretty.GET,
                           url_node_configuration_site_id_format_string.format(site=badock_site.upper(), id=3),
                           body=json.dumps(actual_node_config),
                           content_type="application/json")


class MockedImportPrefectTests(TestCase):
    @staticmethod
    def mock_api_request_basic_node_state_json():
        return json.dumps(basic_node_state)

    @staticmethod
    def mock_api_request_updated_node_state_json():
        updated_node_state = [{'Address': 3, "RoomName": "test_room", "ProgramName": "", "SetPointTemperature": 22.2,
                               "TemperatureAdjustment": 0, "CurrentTemperature": 12, 'L1On': True, 'L2On': False,
                               'AdjustedAtReceiver': True, 'LastReceiveAt': current_time + 60,
                               'PresenceIsDetected': True}]
        return json.dumps(updated_node_state)

    @patch('amqpstorm.basic.Basic.publish')
    @patch('prefect.controllers.prefect.requests')
    def test_detect_setpoint_change(self, mock_req, mock_amqp):
        logger.info('Start')

        mock_req.get.return_value.status_code = 200
        mock_req.get.return_value.json = self.mock_api_request_basic_node_state_json

        logger.info('Creating database models for test')
        # @todo - Create a Site with the name in variable `badock_site_name`
        # @todo - Create a Gateway and a Node too


        c = PrefectController.for_badock()
        c.update(3)

        node = Node.objects.get(gateway__site__name__exact='badock', external_id=3)

        device_type, _ = DeviceType.objects.get_or_create(code=PrefectDeviceType.THERMOSTAT)
        device = Device.objects.get(node=node, type=device_type)

        device_param_type, _ = DeviceParameterType.objects.get_or_create(code=PrefectDeviceParameterType.SETPOINT_TEMP)
        device_param = DeviceParameter.objects.get(device=device, type=device_param_type)

        value_before = device_param.measurements.latest()['value']
        self.assertTrue(value_before == Decimal('21.2'))

        mock_req.get.return_value.json = self.mock_api_request_updated_node_state_json

        c.update(3)
        self.assertTrue(mock_amqp.called)

        # called for each prefect device parameter (thermostat, PIR, 2 x Relay
        self.assertTrue(mock_amqp.call_count == 4)
        # find the call for setpoint change
        th_ = [call[1] for call in mock_amqp.call_args_list if call[1]['type'] == 'TH']
        self.assertTrue(len(th_) == 1)
        setpoint_call = th_[0]
        # check
        self.assertTrue(setpoint_call['previous'] == Decimal('21.2'))
        self.assertTrue(setpoint_call['new'] == Decimal('22.2'))

        value = device_param.measurement.latest()['value']
        assert value == Decimal('22.2')

    def test_decimal_conversion(self):
        """
        Test basic properties of comparing Decimal values

        :return:
        """
        assert Decimal('12') == 12.0
        assert Decimal('12') != None
        assert Decimal('12') == Decimal('12.0')
        self.assertFalse(Decimal('12') != Decimal('12.0'))

    @patch('amqpstorm.Connection')
    @httpretty.activate
    def test_simple(self, connectionMock):
        logger.info('Start', extra={'device': 3, 'site': 'test_site'})
        httpretty.HTTPretty.allow_net_connect = True
        set_up_http_mocks()
        httpretty.HTTPretty.allow_net_connect = True
        c = PrefectController.for_badock()
        c.update(3)
        node = Node.objects.get(gateway__site__name__iexact='badock', external_id=3)

        device_type = DeviceType.objects.get_or_create(code=PrefectDeviceType.RELAY)
        relay_device = Device.objects.filter(node=node, type=device_type).first()

        device_param_type, _ = DeviceParameterType.objects.get_or_create(code=PrefectDeviceParameterType.RELAY_TWO)
        device_param = DeviceParameter.objects.filter(device=relay_device, type=device_param_type).first()
        # device_param = relay_device.

        measurements = device_param.measurements.count()

        assert measurements == 1
        assert device_param.configuration == 2000


actual_node_statii = [{'Address': 190,
                       'AdjustedAtReceiver': False,
                       'CurrentTemperature': 63.1,
                       'L1On': False,
                       'L2On': False,
                       'LastReceiveAt': 1452188104,
                       'ProgramName': 'Automatic Water',
                       'RoomName': 'A Ground Water HWS182',
                       'SetPointTemperature': 50.0,
                       'TemperatureAdjustment': 0.0},
                      {'Address': 191,
                       'AdjustedAtReceiver': False,
                       'CurrentTemperature': 61.8,
                       'L1On': False,
                       'L2On': False,
                       'LastReceiveAt': 1452188105,
                       'ProgramName': 'Automatic Water',
                       'RoomName': 'A Ground Water HWS183',
                       'SetPointTemperature': 50.0,
                       'TemperatureAdjustment': 0.0},
                      {'Address': 192,
                       'AdjustedAtReceiver': False,
                       'CurrentTemperature': 61.4,
                       'L1On': False,
                       'L2On': False,
                       'LastReceiveAt': 1452188106,
                       'ProgramName': 'Emergency Dual Element',
                       'RoomName': 'A Top Water',
                       'SetPointTemperature': 59.0,
                       'TemperatureAdjustment': 9.0}
                      ]
