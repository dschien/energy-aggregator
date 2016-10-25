import calendar
import datetime
import time
import logging
from decimal import Decimal

import pytz
import requests
import simplejson as json
from django.conf import settings
from prefect.controllers.common import BaseController, NodeController

from ep.models import StateChangeEvent, Node, Device, Site, GatewayProperty, DeviceType, Vendor, DeviceParameter, \
    DeviceParameterType, Gateway
from prefect.models import PrefectDeviceParameterType, PrefectDeviceType, device_to_deviceparameter_type_map, \
    device_parameter_type_description_map, devicetype_description_map, unit_map, PrefectDeviceParameterConfiguration

__author__ = 'schien'

logger = logging.getLogger(__name__)

prefect_api_base_url = 'https://pre2000.co.uk/apiv1/SiteApi/'
node_addresses_site_format_url = prefect_api_base_url + '{site}/NodeAddresses'
individual_node_status_url = prefect_api_base_url + '{site}/NodeStatus/{id}'
all_node_stati_url = prefect_api_base_url + '{site}/NodeStatus'
history_days_ago_site_daysAgo_id_format_url = prefect_api_base_url + '{site}/NodeHistory/{daysAgo}/{id}'
url_node_configuration_site_id_format_string = prefect_api_base_url + '{site}/NodeConfiguration/{id}'

badock_site_name = 'badock'
goldney_site_name = 'goldney'

prefect_vendor_name = 'prefect'


class PrefectDeviceController(object):
    POWER_CONSUMPTION_UPDATE_INTERVAL_SECONDS = 500  # usual time is 300s, plus leeway

    def __init__(self, data, device):
        self.device = device
        self.data = data

    def create_measurements(self):
        """
        device_property = models.ForeignKey(DeviceAttribute)
        measurement_time = models.DateTimeField(null=True)
        value

        Create measurement.
        :param data:
        :param device:
        :return:
        """
        seconds_since_unix_epoch = int(time.time())
        last_received_time_since_epoch = self.data['LastReceiveAt'] or seconds_since_unix_epoch
        localized_receive_time = pytz.utc.localize(datetime.datetime.utcfromtimestamp(last_received_time_since_epoch))
        measurement_time = localized_receive_time

        for device_parameter in self.device.parameters.all():
            if device_parameter.type.code == PrefectDeviceParameterType.SETPOINT_TEMP:
                value = Decimal(str(self.data['SetPointTemperature']))
            if device_parameter.type.code == PrefectDeviceParameterType.CURRENT_TEMP:
                value = Decimal(str(self.data['CurrentTemperature']))
            if device_parameter.type.code == PrefectDeviceParameterType.PREFECT_TEMPERATURE_ADJUSTMENT:
                value = Decimal(str(self.data['TemperatureAdjustment']))
            if device_parameter.type.code == PrefectDeviceParameterType.RELAY_ONE:
                value = Decimal(bool(self.data['L1On']))
            if device_parameter.type.code == PrefectDeviceParameterType.RELAY_TWO:
                value = Decimal(bool(self.data['L2On']))
            if device_parameter.type.code == PrefectDeviceParameterType.PIR:
                value = Decimal(bool(self.data['PresenceIsDetected']))

            if device_parameter.type.code == PrefectDeviceParameterType.ENERGY_CONSUMPTION:
                # @todo - return -1 if something went awry
                # @todo - make a note of this in the documentation and ensure that this is shown in visualisation
                if last_received_time_since_epoch > \
                        (seconds_since_unix_epoch - self.POWER_CONSUMPTION_UPDATE_INTERVAL_SECONDS):
                        # Retrieve the enabled state of the configured line
                        config = PrefectDeviceParameterConfiguration.objects.filter(device=self.device).get()
                        line_device_enabled = Decimal(bool(self.data['L1On'])) \
                            if config.line == PrefectDeviceParameterType.RELAY_ONE else Decimal(bool(self.data['L2On']))

                        # Compute power as the product of the configured consumption and the time difference,
                        # iff the line is enabled.
                        latest = device_parameter.measurements.latest()
                        if latest is not None:
                            latest_time_since_unix_epoch = calendar.timegm(
                                datetime.datetime.strptime(latest['time'], "%Y-%m-%dT%H:%M:%SZ").timetuple())
                            dt = last_received_time_since_epoch - latest_time_since_unix_epoch
                        else:
                            logger.debug('No previous measurement found')
                            dt = 1

                        logger.debug('Calculating power consumption for {} using dt={}'.format(self.device, dt))
                        value = config.power_consumption * line_device_enabled * dt
                else:
                    value = -1

            trigger = StateChangeEvent.ON_DEVICE if self.data['AdjustedAtReceiver'] else StateChangeEvent.SCHEDULE

            device_parameter.measurements.add(time=measurement_time, value=value, trigger=trigger)

            logger.info("Storing measurement value {} for device param {} of device {}".format(value,
                                                                                               device_parameter,
                                                                                               self.device),
                        extra={'site': self.device.node.gateway.site.name, 'device': self.device,
                               'type': device_parameter.type, 'device_parameter': device_parameter.id,
                               'current': value, 'trigger': trigger})


class PrefectNodeController(NodeController):
    def __init__(self, json_data, site_name=None, headers=None):
        self.node = None
        self.headers = headers

        self.site_name = site_name
        self.data = json_data

        self.vendor, created = Vendor.objects.get_or_create(name=prefect_vendor_name)
        if created:
            logger.info('Created Vendor: {}'.format(self.vendor))

        self.site, created = Site.objects.get_or_create(name=self.site_name)
        if created:
            logger.info('Created Site: {}'.format(self.site))

        self.gateway, created = Gateway.objects.get_or_create(site=self.site, vendor=self.vendor)
        if created:
            logger.info('Created Gateway: {}'.format(self.gateway))

    def update_node(self) -> Node:
        """
        space_name = models.CharField(max_length=100, null=True)
        floor = models.CharField(max_length=10, null=True)
        building = models.CharField(max_length=50, null=True)
        site = models.CharField(max_length=50, null=True)
        external_id = models.IntegerField()

        :param data:
        :return:
        """

        # gateway = GatewayProperty.objects.filter(gateway__site=site, key='vendor', value=prefect_vendor_name)\
        #     .prefetch_related('gateway').get().gateway

        node, created = Node.objects.get_or_create(external_id=self.data['Address'],
                                                   vendor=self.vendor,
                                                   gateway=self.gateway)
        if created:
            logger.info('Create Node: {}'.format(node))

            # @todo signal or message that new node was created
            node.space_name = self.data['RoomName']
            node.save()

            logger.info("Found new Prefect Node {} in Site {}".format(node.external_id, self.site),
                        extra={'site': node.gateway.site, 'node': node.pk})

            self.create_devices(node)

        self.node = node
        return node

    @staticmethod
    def create_device_configuration(device, line, power_consumption):
        logger.info('Creating PrefectDeviceParameterConfiguration for Device {}. '
                    'The enabled line is {} with a power consumption of {}'.format(device, line, power_consumption))
        dp_config = PrefectDeviceParameterConfiguration.objects.filter(device=device)
        if len(dp_config) > 0:
            dp_config = dp_config.get()
            dp_config.line = line
            dp_config.power_consumption = power_consumption
        else:
            dp_config = PrefectDeviceParameterConfiguration(
                device=device,
                line=line,
                power_consumption=power_consumption
            )
        dp_config.save()

    def create_devices(self, node):
        prefect_id = node.external_id
        site = node.gateway.site

        for device_type_str in [PrefectDeviceType.THERMOSTAT, PrefectDeviceType.PIR, PrefectDeviceType.RELAY]:

            device_type, device_type_created = DeviceType.objects.get_or_create(code=device_type_str)
            if device_type_created:
                if device_type_str in devicetype_description_map:
                    device_type.description = devicetype_description_map[device_type_str]
                    device_type.save()
                logger.info('Created DeviceType: {}'.format(device_type))

            device, device_created = Device.objects.get_or_create(node=node, vendor=self.vendor, type=device_type)
            if device_created:
                logger.info('Create Device: {}'.format(device))

            for device_parameter in device_to_deviceparameter_type_map[device_type_str]:
                device_parameter_type, parameter_type_created = DeviceParameterType.objects.get_or_create(code=device_parameter)
                if parameter_type_created:
                    if device_parameter_type.code in device_parameter_type_description_map:
                        device_parameter_type.description = \
                            device_parameter_type_description_map[device_parameter_type.code]
                        device_parameter_type.save()
                    logger.info('Created DeviceParameterType: {}'.format(device_parameter_type))

                device_parameter, parameter_created = DeviceParameter.objects.get_or_create(device=device,
                                                                                  type=device_parameter_type)
                if parameter_created:
                    if device_parameter_type.code in unit_map:
                        device_parameter.unit = unit_map[device_parameter_type.code]
                        device_parameter.save()
                    logger.info('Created DeviceParameter: {}'.format(device_parameter))

            logger.info("Retrieving node configuration for prefect device {} in site {}".format(prefect_id, site),
                        extra={'site': node.gateway.site, 'device': node.pk})

            if device_type.code == PrefectDeviceType.RELAY:
                url = url_node_configuration_site_id_format_string.format(site=site.name.upper(), id=prefect_id)
                r = requests.get(url, headers=self.headers)
                if r.status_code == 200:
                    res = json.loads(r.content)

                    for device_parameter in device.parameters.all():
                        if device_parameter.type.code == PrefectDeviceParameterType.RELAY_ONE:
                            # This relay is configured to 0, assume it's the other relay (RELAY_TWO)
                            if res[0]['L1LoadWatts'] == 0:
                                self.create_device_configuration(device, PrefectDeviceParameterType.RELAY_TWO,
                                                                 res[0]['L2LoadWatts'])

                        if device_parameter.type.code == PrefectDeviceParameterType.RELAY_TWO:
                            # This relay is configured to 0, assume it's the other relay (RELAY_ONE)
                            if res[0]['L2LoadWatts'] == 0:
                                self.create_device_configuration(device, PrefectDeviceParameterType.RELAY_ONE,
                                                                 res[0]['L1LoadWatts'])
                else:
                    logger.info(
                        "Retrieving node configuration returned with code {} and message {}".format(r.status_code,
                                                                                                    r.content),
                        extra={'site': node.gateway.site, 'device': node.pk})

    def get_device_controllers(self) -> [PrefectDeviceController]:
        return [PrefectDeviceController(self.data, device) for device in self.node.devices.all()]


class PrefectController(BaseController):

    @classmethod
    def by_site_name(cls, site):
        if site.lower() == badock_site_name:
            return cls.for_badock()
        return cls.for_goldney()

    @classmethod
    def for_site(cls, site_name, token):

        instance = cls()
        instance.site = site_name
        instance.headers = {'Authorization': 'Bearer %s' % token}
        return instance

    @classmethod
    def for_badock(cls):
        return cls.for_site(badock_site_name, settings.PREFECT_API_TOKEN_BADOCK)

    @classmethod
    def for_goldney(cls):
        return cls.for_site(goldney_site_name, settings.PREFECT_API_TOKEN_GOLDNEY)

    def get_api_data(self, api_id=None) -> [json]:
        res = None
        if api_id:
            url = individual_node_status_url.format(site=self.site.upper(), id=api_id)
            r = requests.get(url, headers=self.headers)
            if r.status_code == 200:
                res = r.json()
            else:
                logger.warn('Call returned HTTP code: {}'.format(r.status_code))
        else:
            url = all_node_stati_url.format(site=self.site.upper())
            r = requests.get(url, headers=self.headers)
            if r.status_code == 200:
                res = json.loads(r.content)
            else:
                logger.warn('Call returned HTTP code: {}'.format(r.status_code))
        return res

    def get_node_controllers(self, api_data: [json]) -> [PrefectNodeController]:
        node_controllers = []
        if api_data is None:
            logger.error('API call returned None. Check the authorization token.')
            return None
        for el in api_data:
            node_controllers.append(PrefectNodeController(el, site_name=self.site, headers=self.headers))
        return node_controllers

    def get_node_status(self, node_id: int) -> json:
        url = individual_node_status_url.format(site=self.site.upper(), id=node_id)
        logger.debug('Calling {}'.format(url))
        r = requests.get(url, headers=self.headers)
        res = json.loads(r.content)
        return res[0]
