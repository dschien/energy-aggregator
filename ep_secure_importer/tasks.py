import logging
from datetime import date, timedelta

from celery import shared_task
from ep.tasks import ErrorLoggingTask
from ep_secure_importer.controllers.secure_client import SecureClient
from ep_site import settings

__author__ = 'mitchell'
logger = logging.getLogger(__name__)


def datetime_15_minutes_ago_string():
    return (date.today() - timedelta(minutes=15)).strftime('%Y-%m-%dT%H:%M:%S.%f0')


@shared_task(base=ErrorLoggingTask)
def check_gateways_online():
    """
    Checks the online status of all Secure Gateways by retrieving their data
    for the past 15 minutes and examining the GCS flag
    """
    for server_name in settings.SECURE_SERVERS.keys():
        client = SecureClient(server_name)
        client.check_gateways_online(datetime_15_minutes_ago_string())
