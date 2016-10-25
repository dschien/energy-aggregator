import logging

from autobahn.twisted.websocket import WebSocketClientFactory, WebSocketClientProtocol, connectWS
from twisted.internet import reactor
from twisted.internet.protocol import ReconnectingClientFactory

logger = logging.getLogger(__name__)


class AliveLoggingReceivingCallbackWebsocketClientProtocol(WebSocketClientProtocol):
    """
    Receive only websocket client that

    - logs an alive message while connected
    - periodically calls a health check function

    """
    alive = False
    callback = None
    alive_message = 'Secure importer alive.'
    tick_interval = 60
    heartbeat_limit = 5

    def onMessage(self, payload, isBinary):
        if not isBinary:
            # print("Text message received: {}".format(payload.decode('utf8')))
            success = self.callback(payload)
            if not success:
                self.factory.relogin()

    def check_health(self):
        """
        Disconnect the websocket if out of protocoll (application level) health check function returns False.

        :return:
        """
        if self.alive:
            try:
                if not self.health_check_func():
                    logger.info("[Protocol] Reconnecting websocket")
                    self.factory.connector.disconnect()
            except Exception as e:
                logger.exception("[Protocol] error in health check %s" % e)
            reactor.callLater(ReloginReconnectingClientFactory.health_check_interval, self.check_health)

    def log_alive(self):
        """
        Log alive flag every interval
        :return:
        """
        if self.alive:
            logger.info(self.alive_message)
            reactor.callLater(ReloginReconnectingClientFactory.log_alive_interval, self.log_alive)

    def connectionMade(self):
        """
        Start logging when connected
        :return:
        """
        self.alive = True
        logger.info('[Protocol %s] connected to websocket' % id(self))

        reactor.callLater(3, self.log_alive)
        reactor.callLater(3, self.check_health)

        # reset retries variable in ReconnectingClientFactory
        self.factory.resetDelay()
        self.heartBeatCounter = 0

        reactor.callLater(1, self.tick)
        super().connectionMade()

    def connectionLost(self, reason):
        logger.info('[Protocol %s] connection lost ' % id(self))
        self.alive = False

    def tick(self):
        if self.alive:
            self.heartBeatCounter += 1
            logger.info('[Protocol %s] incrementing tick to %s' % (id(self), self.heartBeatCounter))

            if self.heartBeatCounter > self.heartbeat_limit:
                logger.info(
                    '[Protocol {}] no ping for {} * {} seconds -> disconnecting'.format(id(self), self.heartbeat_limit,
                                                                                        self.tick_interval))
                self.transport.loseConnection()
                # self.factory.connector.disconnect()
                return  # do not schedule another tick

            reactor.callLater(self.tick_interval, self.tick)

    def onConnect(self, response):
        logger.info("Connection established: {}".format(self.peer, self.heartBeatCounter))
        super().onConnect(response)

    def onClose(self, wasClean, code, reason):
        logger.warn("[Protocol {0}] WebSocket connection closed. Reason: {1}".format(id(self), reason))
        super().onClose(wasClean, code, reason)

    def onOpen(self):
        super().onOpen()

    def onPing(self, payload):
        self.heartBeatCounter = 0
        logger.info("[Protocol {}] Ping received from {}. Resetting heartbeat counter".format(id(self), self.peer))
        super().onPing(payload)


class ReloginReconnectingClientFactory(ReconnectingClientFactory):
    """
    Changes the websocket server address for a running client.
    """
    health_check_interval = 300
    log_alive_interval = 300

    def __init__(self, *args, login_func=None, **kwargs):
        self.login_func = login_func
        super().__init__(*args, **kwargs)

    def relogin(self):
        logger.info('[Factory] logging in again')
        # get the new address
        ws_url = self.login_func()
        # prepare the factory
        self.setSessionParameters(ws_url)
        # disconnect to trigger re-login
        self.connector.disconnect()


class CallbackProtocolFactory(ReloginReconnectingClientFactory, WebSocketClientFactory):
    protocol = AliveLoggingReceivingCallbackWebsocketClientProtocol

    maxDelay = 10
    maxRetries = 100
    attempt = 0

    def __init__(self, *args, websocketCallback=None, health_check_func=None, **kwargs):
        self.callback = websocketCallback
        self.health_check_func = health_check_func
        super().__init__(*args, **kwargs)

    def startedConnecting(self, connector):
        logger.info('Started to connect.')

    def clientConnectionLost(self, connector, reason):
        self._p.alive = False

        logger.info('Lost connection. Reason: {}'.format(reason))

        self.attempt += 1
        logger.info('Relogin attempt {}'.format(self.attempt))

        self.relogin()

        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        logger.info('[Factory] Connection failed. Reason: {}'.format(reason))
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

    def buildProtocol(self, addr):
        self._p = WebSocketClientFactory.buildProtocol(self, addr)
        self._p.callback = self.callback
        self._p.health_check_func = self.health_check_func
        return self._p


def run(ws_url, message_callback, login_func, health_check_func):
    """

    :param ws_url:
    :param message_callback: to run with any message received from the websocket
    :param login_func: perform a login to get the websocket url
    :param health_check_func: to run periodically to check health of the websocket
    :return:
    """
    logger.debug("connecting to url: %s" % ws_url)
    factory = CallbackProtocolFactory(ws_url, websocketCallback=message_callback, login_func=login_func,
                                      health_check_func=health_check_func)
    connector = connectWS(factory)
    factory.connector = connector
    reactor.run()
