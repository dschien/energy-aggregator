"""
All of the tests here require that the DBs are available. That means, at least the PG and the influxdb containers
 must be running.
"""
import logging
from datetime import timezone, datetime

from decimal import Decimal
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from djcelery.models import PeriodicTask
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from ep.apiviews import uob_estates_group
from ep.models import Device, Node, DeviceParameter, Site, Gateway, Tariff, \
    ScheduleDeviceParameterGroup
# from ep.tests.static_factories import SiteFactory, factory_devices
from ep.tests.factories import SiteFactory, TariffFactory

logger = logging.getLogger(__name__)

# This is a testing site used by the mock_secure_server
# It is defined in ep_secure_importer.controllers.secure_client
test_site = 'secure_testsite'

test_room = 'TestRoom'

node_count = 3

email = "test@example.com"


@override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                   CELERY_ALWAYS_EAGER=True,
                   BROKER_BACKEND='memory')
class BasicAPITestCase(TestCase):
    # fixtures = ['ep_test_data.json', ]

    @classmethod
    def setUpTestData(cls):
        cls.fixture_device_count = len(Device.objects.all())
        SiteFactory.create(name=test_site)

        user = User.objects.create(email=email, username=email)
        g, _ = Group.objects.get_or_create(name=uob_estates_group)
        g.user_set.add(user)

    def test_get_device_measurements(self):
        """
        Basic test that the API returns a list of measurements
        :return:
        """
        token = Token.objects.get(user__username=email)
        # print(len(DeviceParameter.objects.all()))
        # print([i.id for i in DeviceParameter.objects.all()])
        # print(factory_devices[0])
        # print(factory_devices)
        device_param = DeviceParameter.objects.first()
        measurement_count = device_param.measurements.count()
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        url = reverse('api:device_measurements', kwargs={'device_parameter_id': device_param.id})

        response = client.get(url, format='json')

        self.assertTrue(response.status_code == 200)
        self.assertTrue(len(response.data) >= measurement_count)

    def test_get_device_measurements_latest(self):
        """
        Basic test that the API returns a list of measurements
        :return:
        """
        token = Token.objects.get(user__username=email)
        # print(len(DeviceParameter.objects.all()))
        # print([i.id for i in DeviceParameter.objects.all()])
        # print(factory_devices[0])
        # print(factory_devices)
        device_param = DeviceParameter.objects.first()
        device_param.measurements.add(time=datetime.now(), value=Decimal(1))
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        url = reverse('api:device_measurements_latest', kwargs={'pk': device_param.id})

        response = client.get(url, format='json')

        self.assertTrue(response.status_code == 200)
        self.assertTrue('value' in response.data)

    def test_token_required(self):
        """
        Test a token is required to use the API
        :return:
        """
        client = APIClient()

        device = DeviceParameter.objects.first()
        device_parameter_id = device.id

        response = client.get(
            reverse('api:device_measurements', kwargs={'device_parameter_id': device_parameter_id}),
            format='json')
        print(response.status_code)
        self.assertTrue(response.status_code == 401)

    def test_list_all_nodes(self):
        """
        Test
        :return:
        """
        token = Token.objects.get(user__username=email)
        num_devices = len(Node.objects.all())
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        site_id = Site.objects.get(name=test_site).id
        response = client.get(reverse('api:site_nodes', kwargs={'pk': site_id}), format='json')
        self.assertTrue(response.status_code == 200)
        self.assertTrue(len(response.data) == num_devices)

    def test_list_all_sites(self):
        """
        Test
        :return:
        """

        token = Token.objects.get(user__username=email)
        num_LES = len(Site.objects.all())

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = client.get(reverse('api:site_list'), format='json')
        self.assertTrue(response.status_code == 200)
        self.assertTrue(len(response.data) == num_LES)

    def test_list_all_gateways(self):
        """
        Test
        :return:
        """

        token = Token.objects.get(user__username=email)
        site = Site.objects.get(name=test_site)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = client.get(reverse('api:gateway_for_site', kwargs={'pk': site.id}), format='json')
        self.assertTrue(response.status_code == 200)
        self.assertTrue(len(response.data) == len(Gateway.objects.filter(site=site)))

    def test_list_all_devices(self):
        """
        Test
        :return:
        """

        token = Token.objects.get(user__username=email)
        site = Site.objects.get(name=test_site)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = client.get(reverse('api:site_devices', kwargs={'pk': site.id}), format='json')
        self.assertTrue(response.status_code == 200)
        i = len(Device.objects.filter(node__gateway__site=site))

        self.assertTrue(len(response.data) > 0)
        self.assertTrue(len(response.data) == i)

    def test_list_empty_site(self):
        token = Token.objects.get(user__username=email)
        site = Site.objects.create(name='empty')
        site.save()

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = client.get(reverse('api:site_devices', kwargs={'pk': site.id}), format='json')
        self.assertTrue(response.status_code == 200)

        self.assertTrue(len(response.data) == 0)

    def test_list_devices_per_les(self):
        """
        Test
        :return:
        """

        token = Token.objects.get(user__username=email)
        site = Site.objects.filter(name=test_site).first()
        gateway = Gateway.objects.get(site=site)
        num_devices = len(Node.objects.filter(gateway=gateway.pk))
        assert num_devices > 0
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = client.get(reverse('api:site_nodes', kwargs={'pk': site.pk}), format='json')
        self.assertTrue(response.status_code == 200)
        print(response.content)
        self.assertTrue(len(response.data) == num_devices)

    def test_les_details(self):
        """
        Test
        :return:
        """

        site = Site.objects.filter(name=test_site).first()
        token = Token.objects.get(user__username=email)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = client.get(reverse('api:site_details', kwargs={'pk': site.pk}), format='json')
        self.assertTrue(response.status_code == 200)
        self.assertTrue(response.data['name'] == test_site)

    def test_get_node_details(self):
        """
        Test
        :return:
        """
        token = Token.objects.get(user__username=email)
        dp = DeviceParameter.objects.first()

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = client.get(reverse('api:dp_details', kwargs={'pk': dp.pk}), format='json')
        self.assertTrue(response.status_code == 200)
        self.assertTrue(response.data['id'] == dp.pk)

    def test_get_tariff_list(self):
        """
        Basic test that the API returns a list of measurements
        :return:
        """
        token = Token.objects.get(user__username=email)
        TariffFactory.create()
        TariffFactory.create()

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        url = reverse('api:tariff_list')

        response = client.get(url, format='json')

        self.assertTrue(response.status_code == 200)
        self.assertTrue(len(response.data) == 2)

    def test_get_tariff_details(self):
        """
        Basic test that the API returns a list of measurements
        :return:
        """
        token = Token.objects.get(user__username=email)
        TariffFactory.create(name='default')
        tariff = Tariff.objects.first()

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        url = reverse('api:tariff_details', kwargs={'pk': tariff.pk})

        response = client.get(url, format='json')

        self.assertTrue(response.status_code == 200)
        # print(response.data)
        self.assertTrue(response.data['name'] == 'default')

    def test_get_schedules(self):
        token = Token.objects.get(user__username=email)

        # SiteFactory.create(name=test_site)
        first = DeviceParameter.objects.all().first()

        s = ScheduleDeviceParameterGroup()
        s.save()
        s.device_parameters.add(first)

        for task in PeriodicTask.objects.all():
            print(task)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        url = reverse('api:get_device_parameter_schedule', kwargs={'pk': first.pk})
        response = client.get(url, format='json')

        self.assertTrue(response.status_code == 200)
        print(response.data)
        # self.assertTrue(response.data['name'] == 'default')

    def test_get_schedules_id(self):
        token = Token.objects.get(user__username=email)

        # SiteFactory.create(name=test_site)
        first = DeviceParameter.objects.all().first()

        s = ScheduleDeviceParameterGroup()
        s.save()
        s.device_parameters.add(first)

        for task in PeriodicTask.objects.all():
            print(task)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        url = reverse('api:get_device_parameter_schedule', kwargs={'pk': first.pk})
        response = client.get(url, format='json')

        self.assertTrue(response.status_code == 200)
        print(response.data)
        # self.assertTrue(response.data['name'] == 'default')

# class MessageTestCase(TestCase):
#     @classmethod
#     def setUpTestData(cls):
#         SiteFactory.create(name=secure_site_name)
#
#     @patch('ep.signals.device_parameter_state_change.send_robust')
#     @httpretty.activate
#     def test_detect_setpoint_change(self, mock):
#         device_parameter_state_change.send_robust(sender=self.__class__,
#                                                   device_parameter_id=123,
#                                                   type='test setting',
#                                                   previous='previous',
#                                                   new='new value',
#                                                   trigger='test trigger')
#
#         self.assertTrue(mock.called)
#         self.assertTrue(mock.call_count == 1)
#         self.assertTrue(mock.call_args_list[0][1]['trigger'] == 'test trigger')
