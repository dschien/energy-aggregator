import re

import requests
import simplejson as json

from ep.models import Site, Gateway, Node, NodeProperty, Device, DeviceParameter, DeviceParameterType, DPMeasurements, \
    Vendor, DeviceType

import logging

logger = logging.getLogger(__name__)

__author__ = 'mitchell'

rayleigh_site_name = 'rayleigh'
rayleigh_vendor_name = 'rayleigh'
rayleigh_gateway_id = 'rayleigh'
rayleigh_devicetype_name = 'RAYLEIGH'
rayleigh_devicetype_description = 'Rayleigh Connect Sensor'

sensor_type_map = {
    'kwh': {'code': 'POWER', 'description': 'Energy', 'unit': 'kWh'},
    'v3p': {'code': 'VOLTAGE', 'description': 'Voltage, 3-phase', 'unit': 'V', 'split': 3},
    'i3p': {'code': 'CURRENT', 'description': 'Current, 3-phase', 'unit': 'A', 'split': 3},
}

default_rayleigh_api_host = 'api.rayleighconnect.net'
rayleigh_api_uri = 'https://{host}/consumer/v1/{client_id}/{path}.json?app_id={app_id}&access_token={access_token}{extra_args}'


# Creates a CSV string from the keys
# of a dictionary
def make_csv(items):
    csv = ''
    first = True
    for item in items.keys():
        if first:
            first = False
        else:
            csv += ','
        csv += item
    return csv


class RayleighClient(object):
    def __init__(self, client_id="", api_token="", app_id="", host=default_rayleigh_api_host):
        self.client_id = client_id
        self.api_token = api_token
        self.app_id = app_id
        self.host = host

        self.headers = {'Accept': 'application/json'}

        self.rayleigh_site, created = Site.objects.get_or_create(name=rayleigh_site_name)
        if created:
            logger.info('Created new Rayleigh Site: {}'.format(rayleigh_site_name))

        self.rayleigh_vendor, created = Vendor.objects.get_or_create(name=rayleigh_vendor_name)
        if created:
            logger.info('Created new Rayleigh Vendor: {}'.format(rayleigh_vendor_name))

        self.rayleigh_gw, created = Gateway.objects.get_or_create(site=self.rayleigh_site,
                                                                  external_id=rayleigh_gateway_id,
                                                                  vendor=self.rayleigh_vendor)
        if created:
            logger.info('Created new Rayleigh Gateway: {}'.format(rayleigh_gateway_id))

    # Perform an API call to the Rayleigh Connect host
    def consumer_api_call(self, path="", extra=""):
        """
        Performs a HTTP GET request to the Rayleigh Connect API

        :param path: The API endpoint
        :param extra: Extra GET variables to pass - this should begin with an ampersand (&)
        :return: The results and the request object
        """
        url = rayleigh_api_uri.format(
            host=self.host,
            client_id=self.client_id,
            path=path,
            app_id=self.app_id,
            access_token=self.api_token,
            extra_args=extra
        )

        logger.debug('Calling Rayleigh Connect API at URL {}'.format(url))
        req = requests.get(url, headers=self.headers)

        if not req.status_code == 200:
            logger.warn('Rayleigh Connect API call returned with status {}'.format(req.status_code))
            return None, req

        res = json.loads(req.content)

        return res, req

    def process_device(self, device):
        """
        Creates a Node object for the Rayleigh Device

        :param device: The Rayleigh Device data, retrieved from the API
        """
        device_id = device['id']

        node, created = Node.objects.get_or_create(
            gateway=self.rayleigh_gw,
            external_id=device_id,
            vendor=self.rayleigh_vendor
        )
        if created:
            logger.debug('Created device node for {device}'.format(device=device_id))

        for device_prop in device.keys():
            self.process_device_property(device, node, device_prop)

    @staticmethod
    def process_device_property(device, node, device_prop):
        """
        Add all properties to the Node as metadata

        :param device: The Rayleigh Device data, retrieved from the API
        :param node: The Node object created or retrieved from the database for the Rayleigh Device
        :param device_prop: The property name, a key to the Rayleigh Device data
        """
        device_id = device['id']
        value = device[device_prop]

        prop, created = NodeProperty.objects.get_or_create(
            node=node,
            key=device_prop
        )

        if created:
            logger.debug('Created property {prop} for device {device}'.format(prop=device_prop, device=device_id))

        if (not hasattr(prop, 'value')) or (str(prop.value) != str(value)):
            logger.debug(
                'Updating value of property {prop} from {old} to {val}'.format(prop=device_prop, old=prop.value,
                                                                               val=value))
            prop.value = value
            prop.save()

    def retrieve_devices(self):
        """
        Retrieve a list of devices and store them in the meta database

        An example device is a PV installation on a specific building
        :return: A list of devices from the API
        """
        devices, req = self.consumer_api_call(path='devices')
        if devices is None:
            logger.warn('Something went wrong, aborting')
            return

        for device in devices:
            self.process_device(device)
        return devices

    @staticmethod
    def extract_id_and_param(sensor_key):
        """
        Extracts the ID and the parameter name from the key returned by the API call

        :param sensor_key: The dictionary key returned for sensor data
        :return: The Rayleigh Device ID and the parameter name
        """
        m = re.search('(e\d+)(.(\w+))*', sensor_key)

        device_id = None
        param = None
        if m is not None:
            device_id, param = m.group(1, 3)

        return device_id, param

    @staticmethod
    def add_sensor_device(type_code, type_description, sensor_type, sensor_device, value=None):
        sensor_device_type, created = DeviceParameterType.objects.get_or_create(
            code=type_code,
            description=type_description
        )
        if created:
            logger.debug('Created DeviceParameterType: {}'.format(sensor_device_type))

        device_param, created = DeviceParameter.objects.get_or_create(
            device=sensor_device,
            type=sensor_device_type,
            unit=sensor_type['unit']
        )
        if created:
            logger.debug('Created DeviceParameter: {}'.format(device_param))

        if value is not None:
            DPMeasurements(device_param).add(DPMeasurements.time(), value)

    def retrieve_sensors(self, device):
        """
        Retrieve a list of sensors from a specified device and store them in the meta database

        An example sensor is a particular PV panel
        :param device: A Node object describing a Rayleigh Device
        """
        device_id = device.external_id
        path = 'devices/' + device_id
        res, req = self.consumer_api_call(path=path)
        if res is None:
            logger.warn('Something went wrong, aborting')
            return

        params = {}
        sensors = res[device_id]

        # @todo - Create Devices for temperature
        # Caveat: is this a Device or a DeviceParameter? If the latter, for what Device?

        # # Check for temperature readout
        # # This is non-English (Spanish or Italian)
        # if 'name' in sensor:
        #     m = re.search('Temperatura (\w+)', sensor['name'])
        #     if m is not None:
        #         logger.debug('Found temperature reading {name} {value}'.format(
        #             name=sensor['name'], value=sensor['last_value']))

        # Create any Devices (sensors)
        for sensor_key in sensors.keys():
            sensor = sensors[sensor_key]
            sensor_id, param = self.extract_id_and_param(sensor_key)

            if sensor_id is not None:
                if param is None:
                    sensor_device_type, created = DeviceType.objects.get_or_create(
                        code=rayleigh_devicetype_name,
                        description=rayleigh_devicetype_description,
                    )
                    if created:
                        logger.debug('Created DeviceType: {}'.format(sensor_device_type))

                    sensor_device, created = Device.objects.get_or_create(
                        node=device,
                        vendor=self.rayleigh_vendor,
                        type=sensor_device_type,
                        external_id=sensor_id,
                        name=sensor['name']
                    )
                    if created:
                        logger.debug('Created Device: {}'.format(sensor_device))
                else:
                    # Add it to a list and wait until all other sensors have been processed
                    params[sensor_key] = sensor

        # Create any DeviceParameters (sensor parameters) for the sensor Devices
        for sensor_key in params.keys():
            sensor_param = sensors[sensor_key]
            sensor_id, param = self.extract_id_and_param(sensor_key)

            sensor_device = Device.objects.filter(
                node=device,
                vendor=self.rayleigh_vendor,
                external_id=sensor_id
            ).get()

            if sensor_device is None:
                logger.error('Could not find matching sensor for parameter {}'.format(sensor_key))
            else:
                if param in sensor_type_map:
                    sensor_type = sensor_type_map[param]

                    # Does the parameter need splitting?
                    if 'split' in sensor_type:
                        # Adjusted for 0-indexing
                        n = sensor_type['split'] - 1

                        # Re-adjusted for clarity
                        logger.debug('Sensor parameter is divided into {} parts'.format(n+1))

                        # Re-adjusted for inclusive range
                        for i in range(0, n+1):
                            addendum = ' ({} of {})'.format(i+1, n+1)
                            type_code = sensor_type['code'] + addendum
                            type_description = sensor_type['description'] + addendum

                            logger.debug('Using type_code {} and type_description {}'.format(type_code, type_description))

                            value = None
                            if 'last_value' in sensor_param:
                                value = sensor_param['last_value']
                                if type(value) is list:
                                    value = value[i]

                            self.add_sensor_device(type_code, type_description, sensor_type, sensor_device,
                                                   value)

                    else:
                        value = None
                        if 'last_value' in sensor_param:
                            value = sensor_param['last_value']

                        self.add_sensor_device(sensor_type['code'], sensor_type['description'], sensor_type, sensor_device,
                                               value)

        return sensors

    def retrieve_sensor_readings(self, device, sensors, start, end):
        """
        Retrieve archival data for a specified list of sensors from a single device, storing the readings
        in the time series database

        An example reading is the energy generated in kwh

        :param device: a Node object describing a Rayleigh Device
        :param sensors: a list of Devices describing Rayleigh sensors
        :param start: a timestamp for the beginning of the required data, in ms from Jan. 1st 1970
        :param end: a timestamp for the end of the required data, in ms from Jan. 1st 1970
        """
        device_id = device.external_id
        path = 'data/' + device_id + ':(' + make_csv(sensors) + ')'
        extra = '&from=' + start + '&to=' + end

        res, req = self.consumer_api_call(path=path, extra=extra)
        if res is None:
            logger.warn('Something went wrong, aborting')
            return

        sensors = res[device_id]
        for sensor_id in sensors.keys():
            readings = sensors[sensor_id]

            sensor_devices = Device.objects.filter(
                node=device,
                external_id=sensor_id
            )
            if len(sensor_devices) == 0:
                continue

            sensor_device = sensor_devices.get()
            for reading in readings:
                time = reading[0]
                value = reading[1]
                logger.debug('Adding sensor reading for {sensor}: {time} {value}'.format(sensor=sensor_id, time=time, value=value))
                DPMeasurements(sensor_device).add(time, value)

        return sensors
