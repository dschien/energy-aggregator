import datetime
import logging
from functools import partial

import simplejson as json
from django.core.management import BaseCommand

from ep_secure_importer.controllers.secure_client import SecureClient
from ep_secure_importer.controllers.websocket_client import run

__author__ = 'schien'

logger = logging.getLogger(__name__)
error_email_logger = logging.getLogger('management_commands')


class ConnectionException(Exception):
    pass


def websocket_message_processing_callback(message, secure_server_name=None):
    """
    Callback to pass to the websocket protocol
    :return:
    """

    res = json.loads(message)
    logger.debug("Received push message from websocket")
    if res['DataType'] == 0:
        SecureClient.process_push_data(res['Data'])
        return True
    else:
        logger.info("Received error from websocket", extra={'data': json.dumps(res), "server": secure_server_name})
        logger.info("Restarting websocket listener")

        return False


class Command(BaseCommand):
    help = 'Import now'
    old_map = None
    gateway_last_healthy_update_time = None

    def add_arguments(self, parser):
        parser.add_argument('-r', '--reset-mc', action='store_true', default=False)
        parser.add_argument('-s', action='store', default=False)

    def handle(self, *args, **options):
        self.secure_server_name = options['s']

        if options['reset_mc']:
            SecureClient.delete_auth_tokens(self.secure_server_name)
        try:
            websocket_message_callback = partial(websocket_message_processing_callback,
                                                 secure_server_name=self.secure_server_name)

            websocket_login_func = partial(Command.get_ws_url, secure_server_name=self.secure_server_name)

            ws_url = websocket_login_func()
            run(ws_url, websocket_message_callback, websocket_login_func, self.check_gateway_online)

        except Exception:
            error_email_logger.exception('Exception in %s secure importer' % self.secure_server_name)
            logger.info('sleeping for remote recovery')

    @staticmethod
    def get_ws_url(secure_server_name='default'):
        ak, ak_id = SecureClient(secure_server_name).get_auth_tokens(reset=True)
        ws_url = SecureClient.get_websocket_url(ak, ak_id, secure_server_name)
        return ws_url

    @staticmethod
    def datetime_now_string():
        return datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f0')

    def check_gateway_online(self):
        """
        Implements the health check for check_health function in AliveLoggingReceivingCallbackWebsocketClientProtocol.

        Must return True if healthy, False otherwise -> triggers disconnection from websocket (and reconnection attempt).

        :return:
        """
        self.gateway_last_healthy_update_time = self.datetime_now_string()
        healthy, new_map = SecureClient(self.secure_server_name).check_gateways_online(
            self.gateway_last_healthy_update_time)

        # check whether a previously offline gateway is now online
        # the first time this is run, skip
        if self.old_map:
            new_map_hash = hash(frozenset(new_map.items()))
            old_map_hash = hash(frozenset(self.old_map.items()))

            if not old_map_hash == new_map_hash:
                # restart the websocket
                logger.info('Secure server %s reports a change in gateway online status' % self.secure_server_name,
                            extra={"server": self.secure_server_name})
                return False

        # store the old map for the next iteration
        self.old_map = new_map

        if healthy:
            self.gateway_last_healthy_update_time = self.datetime_now_string()
            logger.info('Secure server %s reports that all gateways are online' % self.secure_server_name,
                        extra={"server": self.secure_server_name})
            return True

        logger.warn('One or more gateways are offline on server %s' % self.secure_server_name,
                    extra={"server": self.secure_server_name})
        return True
