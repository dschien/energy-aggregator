import pytz

bst = pytz.timezone('Europe/London')

import json
import logging
import time
import datetime
from decimal import Decimal
from unittest.mock import patch, MagicMock

from celery import current_app
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test import override_settings
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from ep.apiviews import uob_estates_group, ebe_group
from ep.tests.factories import SiteFactory, DeviceFactory
from ep_secure_importer.controllers.secure_client import SecureClient
from ep_secure_importer.management.commands.import_secure import Command
from ep.models import Device, DeviceParameter, Gateway, Site, GCSMeasurements, Node, SECURE_SERVER_NAME
from ep.tests.test_standalone import email  # , SiteFactory
from ep_secure_importer.models import SecureDeviceType, SecureDeviceParameterType, SecureDeviceParameterActions

__author__ = 'schien'
logger = logging.getLogger(__name__)


class SecureAPITests(TestCase):
    site_name = 'test'
    gw_mac_id = 123
    gateway = None

    @classmethod
    @patch('amqpstorm.Connection')
    def setUpTestData(cls, mock):
        # Create a test user
        user = User.objects.create(email=email, username=email)

        # Add user to the requisite groups
        estates_group_obj, _ = Group.objects.get_or_create(name=uob_estates_group)
        estates_group_obj.user_set.add(user)

        ebe_group_obj, _ = Group.objects.get_or_create(name=ebe_group)
        ebe_group_obj.user_set.add(user)

        settings.CELERY_ALWAYS_EAGER = True
        current_app.conf.CELERY_ALWAYS_EAGER = True

        # Create the requisite models
        # SiteFactory.create(name=SecureAPITests.site_name)
        # site = Site.objects.first()

        actions = SecureDeviceParameterActions()
        actions.save()
        SiteFactory(name=SecureAPITests.site_name, gateway__external_id=cls.gw_mac_id,
                    gateway__vendor__name='secure', gateway__node__device__type__code=SecureDeviceType.SRT321)
        gw = Gateway.objects.first()
        gw.properties.create(key=SECURE_SERVER_NAME, value='test')
        dp = DeviceParameter.objects.first()
        dp.actions = actions
        dp.save()


    def test_factories(self):
        site = Site.objects.first()
        gateway = Gateway.objects.filter(site=site).first()
        node = Node.objects.filter(gateway=gateway).first()
        devices = Device.objects.filter(node=node)
        self.assertTrue(len(devices) > 0)

    def test_get_measurement_history(self):
        """
        Test that more than one push data is put into TS DB and then returned by the
        measurements API function.

        :return:
        """
        device = DeviceFactory(node=Node.objects.first(), external_id='123', type__code=SecureDeviceType.SRT321,
                               device_param__type__code=SecureDeviceParameterType.MEASURED_TEMPERATURE)
        d_id_1 = device.external_id

        now_loc = datetime.datetime.now(bst)
        ts_loc = now_loc - datetime.timedelta(seconds=30)
        ts_str = ts_loc.strftime('%Y-%m-%dT%H:%M:%S')

        data = self.create_secure_server_push_data(d_id_1, ts_str)

        SecureClient.process_push_data(data)
        time.sleep(.5)

        # get newer timestamp
        ts_str = now_loc.strftime('%Y-%m-%dT%H:%M:%S')
        data = self.create_secure_server_push_data(d_id_1, ts_str, value="23.5")

        SecureClient.process_push_data(data)

        token = Token.objects.get(user__username=email)
        device_param = device.parameters.first()
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        url = reverse('api:device_measurements', kwargs={'device_parameter_id': device_param.id})

        time.sleep(.5)

        response = client.get(url, format='json')

        self.assertTrue(response.status_code == 200)
        self.assertTrue(len(response.data) >= 2)

    @staticmethod
    def create_secure_server_push_data(external_device_ref_id, timestamp_string, value="23.7",
                                       dp_type=SecureDeviceParameterType.MEASURED_TEMPERATURE):
        """

        Sythesize a json object identical in its structure to what comes from the secure server over the websocket as push data.

        :param external_device_ref_id:
        :param timestamp_string:
        :param value:
        :param dp_type:
        :return:
        """
        data = {"ALMS": [], "GDDO": {"LUT": timestamp_string, "GMACID": SecureAPITests.gw_mac_id, "GCS": "1",

                                     "ZNDS": [

                                         {"DDDO": [

                                             {"DRefID": external_device_ref_id, "DPID": 64, "DPDO": [

                                                 {"DPRefID": dp_type,
                                                  "CV": value, "LUT": timestamp_string},
                                             ]},

                                         ], "ZID": 1}],
                                     "GN": "IodicusGateway"}}
        return data

    @override_settings(
        SECURE_SERVERS={'test': {'HOST': 'test.com', 'WSHOST': 'test', 'USER': 'tester', 'PASSWORD': 'test'}})
    @patch('ep_secure_importer.controllers.secure_client.mc')
    @patch('amqpstorm.Connection')
    def test_change_setpoint_put(self, mock_amqp, mock_mc):
        """
            Test the put/patch end point for changing setpoints on devices.
            In the deployed system this triggers a message to the messaging.iodicus.net rabbitMQ.
            Here, this is mocked out.

        :return:
        """

        token = Token.objects.get(user__username=email)
        device_parameter = DeviceParameter.objects.first()
        device_parameter.measurements.add(time=timezone.now(), value=Decimal(10))

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        data = {'target_value': 25}
        response = client.put(reverse('api:dp_details', kwargs={'pk': device_parameter.pk}), data,
                              format='json')
        self.assertTrue(response.status_code == 200)

    @override_settings(
        SECURE_SERVERS={'test': {'HOST': 'test.com', 'WSHOST': 'test', 'USER': 'tester', 'PASSWORD': 'test'}})
    @patch('ep_secure_importer.controllers.secure_client.mc')
    @patch('amqpstorm.basic.Basic.publish')
    def test_change_setpoint_patch(self, mock_amqp, mock_mc):
        """
        Test the put/patch end point for changing setpoints on devices.
        In the deployed system this triggers a message to the messaging.iodicus.net rabbitMQ.
        Here, this is mocked out.

        :return:
        """
        self.setup_memcache_mock_auth_data(mock_mc)
        device_parameter = DeviceParameter.objects.first()

        device_parameter.measurements.add(time=timezone.now(), value=Decimal(10))

        token = Token.objects.get(user__username=email)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        self.assertTrue(uob_estates_group in token.user.groups.values_list('name', flat=True))

        data = {'target_value': 25}
        response = client.patch(reverse('api:dp_details', kwargs={'pk': device_parameter.pk}), data,
                                format='json')
        self.assertTrue(response.status_code == 200)

    gw_online = json.dumps({'ALMS': [],
                            'GDDO': {'GCS': '1',
                                     'GMACID': gw_mac_id,
                                     'GN': 'CHANGE_ME',
                                     'LUT': '2016-04-14T12:15:38.335',
                                     'ZNDS': None}})

    gw_offline = json.dumps({'ALMS': [],
                             'GDDO': {'GCS': '0',
                                      'GMACID': gw_mac_id,
                                      'GN': 'CHANGE_ME',
                                      'LUT': '2016-04-14T12:15:38.335',
                                      'ZNDS': None}})

    gateway_list_all = json.dumps([{'GMACID': 46477239136516, 'GN': 'CHANGE_ME', 'GSN': 'CHANGE_ME', 'RID': 2},
                                   {'GMACID': gw_mac_id, 'GN': 'UOBLANGF', 'GSN': 'UOB00011', 'RID': 2},
                                   {'GMACID': 46477239136513, 'GN': 'CHANGE_ME', 'GSN': 'UOBTEST0', 'RID': 2}])

    gateway_list = json.dumps([{'GMACID': gw_mac_id, 'GN': 'CHANGE_ME', 'GSN': 'CHANGE_ME', 'RID': 2}])

    capability_push_response = json.dumps({"ERR": [{"Value": "Smart Home Exception", "ID": 848}], "SUC": False})

    # need to set the name of the server
    @override_settings(
        SECURE_SERVERS={'test': {'HOST': 'test.com', 'WSHOST': 'test', 'USER': 'tester', 'PASSWORD': 'test'}})
    # need to patch requests to the secure server
    @patch('ep_secure_importer.controllers.secure_client.requests')
    # need to bypass login by pre-populating the memcache
    @patch('ep_secure_importer.controllers.secure_client.mc')
    def test_gcs(self, mc_mock, req_mock):
        """
        Test check_gateway_online from gateway communication status

        We expect that a change of gw status is detected.

        :return:
        """

        self.setup_memcache_mock_auth_data(mc_mock)

        def get_method_mock(*args, **kwargs):
            """
            Mocks called urls:

            1. /user/GatewayList
            2. /gateway/gatewaydata?gtMacID="..."&...

            :param args:
            :param kwargs:
            :return:
            """

            gatewaydata_path = 'gatewaydata'
            gateway_list_path = 'GatewayList'

            # comes in form 'http://test.com/section/command' - we want to split to get the command
            path_segment = args[0].split('/')[4].split('?')[0]
            mm = MagicMock()
            mm.status_code = 200

            content = '{"message": "not implemented"}'
            if path_segment == gatewaydata_path:

                if SecureAPITests.mock_call_counter % 2 == 0:
                    print('online')
                    gcs_data = SecureAPITests.gw_online

                if SecureAPITests.mock_call_counter % 2 == 1:
                    print('offline')
                    gcs_data = SecureAPITests.gw_offline

                # special case
                if SecureAPITests.mock_call_counter == 3:
                    gcs_data = SecureAPITests.capability_push_response
                    mm.status_code = 400

                content = gcs_data

                SecureAPITests.mock_call_counter += 1

            if path_segment == gateway_list_path:
                content = SecureAPITests.gateway_list

            mm.content = content

            return mm

        req_mock.get.side_effect = get_method_mock

        site = Site.objects.first()
        gateway = Gateway.objects.filter(site=site).first()

        # run
        c = Command()
        c.secure_server_name = 'test'

        # online
        self.assertTrue(c.check_gateway_online())
        time.sleep(2)
        latest = GCSMeasurements(gateway).latest()

        self.assertTrue(latest['value'] == Decimal(1))
        # offline
        self.assertFalse(c.check_gateway_online())
        time.sleep(2)
        latest = GCSMeasurements(gateway).latest()

        self.assertTrue(latest['value'] == Decimal(0))
        # online
        self.assertTrue(c.check_gateway_online())
        time.sleep(2)
        latest = GCSMeasurements(gateway).latest()

        self.assertTrue(latest['value'] == Decimal(1))

        # capability push -> then online
        self.assertTrue(c.check_gateway_online())
        # offline
        self.assertFalse(c.check_gateway_online())

    def setup_memcache_mock_auth_data(self, mc_mock):
        # mock out the memcache client
        my_dict = {'secure_ak_test': '1', 'secure_ak_id_test': '2'}

        def getitem(name):
            return my_dict[name]

        mc_mock.__getitem__.side_effect = getitem
        mc_mock.__contains__.side_effect = lambda k: True

    mock_call_counter = 0
