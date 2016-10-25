from django.core.management import BaseCommand
from ep.models import DeviceParameter, SECURE_SERVER_NAME, StateChangeEvent

from ep_secure_importer.controllers.secure_client import SecureClient, secure_vendor_name


class Command(BaseCommand):
    help = 'Schedule a device state change'

    def add_arguments(self, parser):
        parser.add_argument('device_parameter_id')
        parser.add_argument('target_value')
        parser.add_argument('-t', '--trigger', default=StateChangeEvent.ON_DEVICE)

    def handle(self, *args, **options):
        device_parameter_id = options['device_parameter_id']
        target_value = options['target_value']
        trigger = options['trigger']

        SecureClient.store_device_state_change_request(device_parameter_id, target_value, trigger)

        device_parameter = DeviceParameter.objects.get(pk=device_parameter_id)
        for prop in device_parameter.device.node.gateway.properties.all():
            if prop.key == 'vendor' and prop.value == secure_vendor_name:
                # @todo test
                secure_server_name = prop.gateway.properties.filter(key=SECURE_SERVER_NAME).get().value
                SecureClient(secure_server_name).change_secure_device_state(device_parameter, target_value)
                break
