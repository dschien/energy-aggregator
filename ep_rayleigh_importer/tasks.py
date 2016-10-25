import logging

from celery import shared_task
from django.conf import settings
from ep.tasks import ErrorLoggingTask
from ep.models import Node

from ep_rayleigh_importer.controllers.rayleigh_client import RayleighClient

__author__ = 'mitchell'
logger = logging.getLogger(__name__)


def make_rayleigh_client():
    """
    Instantiates the RayleighClient class using values taken from the Settings (see docs/SETTINGS.rst for details)
    :return: An instance of the RayleighClient class
    """
    return RayleighClient(
        settings.RAYLEIGH_CLIENT_ID,
        settings.RAYLEIGH_API_TOKEN,
        settings.RAYLEIGH_APP_ID,
        settings.RAYLEIGH_HOST
    )


def get_devices(client):
    """
    Wrapper function for retrieving Rayleigh model objects

    :param client: An instance of the RayleighClient class
    :return: A list of Node objects representing Rayleigh devices
    """
    return Node.objects.filter(gateway=client.rayleigh_gw)


def import_devices(client):
    """
    Imports all devices from the Rayleigh Connect API

    :param client: An instance of the RayleighClient class
    :return: A JSON object containing devices and their parameters, retrieved from the Rayleigh Connect API
    """
    return client.retrieve_devices()


def import_sensors(client):
    """
    Imports sensors from the Rayleigh Connect API for all devices

    :param client: An instance of the RayleighClient class
    :return: A JSON object containing sensor data for each device, retrieved from the Rayleigh Connect API
    """
    devices = get_devices(client)
    sensors = []
    for device in devices:
        device_sensors = import_sensors_from_device(client, device)
        sensors.append(device_sensors)
    return sensors


def import_sensors_from_device(client, device):
    """
    Imports sensor data of specified devices from the Rayleigh Connect API

    :param client: An instance of the RayleighClient class
    :param device: A list of Node objects describing the Rayleigh devices
    :return: A JSON object containing the sensors for each device, retrieved from the Rayleigh Connect API
    """
    return client.retrieve_sensors(device)


@shared_task(base=ErrorLoggingTask)
def import_from_api():
    """
    Imports all devices and sensors from the Rayleigh Connect API
    """
    client = make_rayleigh_client()
    import_devices(client)
    import_sensors(client)


@shared_task(base=ErrorLoggingTask)
def import_historical(start: int, end: int):
    """
    Imports all devices and sensors from the Rayleigh Connect API for a given time period

    :param start: a timestamp for the beginning of the required data, in ms from Jan. 1st 1970
    :param end: a timestamp for the end of the required data, in ms from Jan. 1st 1970
    """
    client = make_rayleigh_client()
    import_devices(client)
    devices = get_devices(client)
    for device in devices:
        sensors = import_sensors_from_device(client, device)
        client.retrieve_sensor_readings(device, sensors, start, end)
