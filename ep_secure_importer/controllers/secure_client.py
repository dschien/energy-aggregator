import base64
import datetime
import hashlib
import hmac
import logging
from decimal import Decimal

import pylibmc
import pytz
import requests
import simplejson as json
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from ep.models import DeviceParameter, StateChangeEvent, DeviceType, Vendor, \
    DeviceParameterType
from ep.models import Site, Gateway, Node, Device, SECURE_SERVER_NAME, GatewayProperty, \
    GCSMeasurements

import ep_secure_importer.models

# import SecureDeviceType, device_parameter_type_description_map, unit_map, \
#     device_to_deviceparameter_type_map, devicetype_description_map, dtype_map, SecureDeviceParameterActions

mc = pylibmc.Client([settings.MEMCACHE_HOST], binary=True, behaviors={"tcp_nodelay": True, "ketama": True})
logger = logging.getLogger(__name__)

secure_vendor_name = 'secure'
secure_site_name = 'secure_testsite'

MAX_CAPABILITY_PUSH_REQUESTS = 10


class SecureClient(object):
    def __init__(self, secure_server_name):
        self.secure_server_name = secure_server_name
        self.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        self.capability_push_request_count = 0

    def change_secure_device_state(self, device_parameter, target_value):
        data = {'GatewayMacId': device_parameter.device.node.gateway.external_id,
                'DeviceData': {'DRefID': device_parameter.device.external_id,
                               'DPID': 64,
                               'DPDO': [
                                   {'DPRefID': device_parameter.type.code,
                                    'CV': target_value,
                                    'LTU': SecureClient.get_dateheader()
                                    }
                               ]}}

        data_str = json.dumps(data)

        self.update_device_data(data_str, device_parameter)

    # defined in NGDCS_WebService_Interface_v1.20 page 31
    SECURE_GCS_CONNECTED = "1"

    def check_gateway_online(self, GMACID, last_update_time):
        res, status_code = self.get_gateway_data(GMACID, last_update_time)

        if status_code != 200:
            logger.warn('Unable to retrieve gateway data fom {}'.format(GMACID))
            return False

        return res['GDDO']['GCS'] == SecureClient.SECURE_GCS_CONNECTED

    def check_gateways_online(self, last_update_time):

        res, status_code = self.get_gateway_list()

        if status_code != 200:
            logger.warn('Unable to retrieve list of gateways from {}'.format(self.secure_server_name))
            return False

        healthy = True
        map = {}

        for gateway in res:
            gmacid = gateway['GMACID']

            this_healthy = self.check_gateway_online(gmacid, last_update_time)
            map[gmacid] = this_healthy
            if this_healthy:
                logger.info('Gateway {} is online'.format(gmacid))
            else:
                logger.warn('Gateway {} is offline'.format(gmacid))
                healthy = False

            # update meta data
            # @todo duplicated property value and measurement in TS
            try:
                gateway_object = Gateway.objects.filter(external_id=gmacid).get()
            except Gateway.DoesNotExist:
                logger.warn('Gateway {} not present in metadata'.format(gmacid))
                continue

            online_property_name = 'online'
            online_property, created = GatewayProperty.objects.get_or_create(gateway=gateway_object,
                                                                             key=online_property_name)
            if created:
                logger.debug('Added new property \'{}\' to gateway {}'.format(online_property_name, gmacid))
            online_property.value = str(this_healthy)
            online_property.save()

            # update TS data
            GCSMeasurements(gateway_object).add(timezone.now(), this_healthy)
        return healthy, map

    def perform_get_request(self, path):
        """
        Performs a GET request to the specified path, first setting the necessary authorization headers.

        :param path: The request path, appended to the server's HOST
        :returns: The response and the HTTP status code of the request
        """
        url = 'http://{server_address}{path}'.format(
            server_address=settings.SECURE_SERVERS[self.secure_server_name]['HOST'], path=path)

        # remove the query variables to sign the naked path
        naked_path = path.split('?', 1)[0]

        ak, ak_id = self.get_auth_tokens()
        self.headers.update(SecureClient.get_extra_headers(ak=ak, ak_id=ak_id, path=naked_path))
        logger.debug("Calling {path}".format(path=path))
        r = requests.get(url, headers=self.headers)

        res = json.loads(r.content)

        if self.is_capability_push(r, res):
            if self.capability_push_request_count < MAX_CAPABILITY_PUSH_REQUESTS:
                self.capability_push_request_count += 1
                return self.perform_get_request(path)
            else:
                logger.error('Timed out due to capability push count exceeding the maximum ({})'.format(
                    MAX_CAPABILITY_PUSH_REQUESTS))
        else:
            self.capability_push_request_count = 0

        logger.debug(
            'Call to http://{server_address}{path} from secure server got response [HTTP Code {code}]'.format(
                server_address=settings.SECURE_SERVERS[self.secure_server_name]['HOST'],
                path=path,
                code=r.status_code),
            extra={'response': json.dumps(res)})

        return res, r.status_code

    def get_gateway_list(self):
        return self.perform_get_request('/user/GatewayList')

    def get_gateway_data(self, gmacid, last_update_time):
        hexmac = hex(gmacid)
        path = '/gateway/gatewaydata?gatewayMACID={gmacid}&lastupdatetime="{lut}"'.format(gmacid=hexmac,
                                                                                          lut=last_update_time)
        return self.perform_get_request(path)

    def update_device_data(self, data_str, device_parameter):
        path = '/Gateway/UpdateDeviceData'
        url = 'http://{server_address}{path}'.format(
            server_address=settings.SECURE_SERVERS[self.secure_server_name]['HOST'], path=path)

        ak, ak_id = self.get_auth_tokens()
        self.headers.update(SecureClient.get_extra_headers(ak=ak, ak_id=ak_id, path=path, data_str=data_str))
        logger.info("Requesting device parameter change",
                    extra={'data': data_str, 'device_parameter': device_parameter.id})
        r = requests.post(url, data=data_str, headers=self.headers)

        try:
            res = r.json()
        except:
            logger.error('Update device data failed. [HTTP Code {}]'.format(r.status_code),
                         extra={'response': json.dumps(r.content)})
            res = None
        logger.debug('Update call to secure server got response [HTTP Code {}]'.format(r.status_code),
                     extra={'response': json.dumps(res)})
        if r.status_code != 200:
            logger.warn("Received error from secure server.", extra={'response': res})

            if self.is_capability_push(r, res):
                return self.update_device_data(data_str, device_parameter)

            logger.error('Update device data failed. [HTTP Code {}]'.format(r.status_code),
                         extra={'response': json.dumps(res)})

        return res, r.status_code

    def is_capability_push(self, r, res):
        if r.status_code == 400 and any([i['ID'] == 848 for i in res['ERR']]):
            logger.warn("Received error 848 from secure server. {}".format(res))
            SecureClient.delete_auth_tokens(self.secure_server_name)
            return True
        return False

    def login(self):
        self.headers.update({'DateHeader': SecureClient.get_dateheader()})
        data = {"UserEMailID": settings.SECURE_SERVERS[self.secure_server_name]['USER'],
                "Password": SecureClient.hash_password(settings.SECURE_SERVERS[self.secure_server_name]['PASSWORD'])}

        url = 'http://{server_address}/user/{command}'.format(
            server_address=settings.SECURE_SERVERS[self.secure_server_name]['HOST'], command='login')
        r = requests.post(url, data=data)

        if r.status_code is not 200:
            raise Exception('HTTP [%s] Error on backend: %s' % (r.status_code, r.content))

        res = json.loads(r.content)
        logger.info("received login data from secure server", extra={'data': json.dumps(res)})

        # Get Session
        ak = res['SSD']['AK']
        ak_id = res['SSD']['AKID']

        # store credentials in memcache
        SecureClient.store_auth_keys(ak, ak_id, self.secure_server_name)

        return ak, ak_id, res

    def get_auth_tokens(self, reset=False):
        auth_key = 'secure_ak_%s' % self.secure_server_name
        if reset:
            SecureClient.delete_auth_tokens(self.secure_server_name)

        if auth_key in mc:
            ak = mc[auth_key]
            ak_id = mc['secure_ak_id_%s' % self.secure_server_name]
        else:
            ak, ak_id, res = self.login()
            self.process_login_data(res)

        return ak, ak_id

    def process_login_data(self, res):
        """
        On login, the server returns the server state - including the configuration of all gateways and connected devices.
        This is the opportunity to update configuration data.

        1.
        :return:
        """
        # Concept of site does not exist for secure -> for new gateway, add them to a "holding" site
        site, _ = Site.objects.get_or_create(name=secure_site_name)

        # @todo Send email if site mapping does not contain entry for this gateway

        # import from all gateways
        for GDDO in res['GDDO']:
            gw_mac = GDDO['GMACID']
            logger.info('Processing login data for gateway %s' % gw_mac, extra={'gw_mac': gw_mac})
            logger.debug('Login message data for gateway %s' % gw_mac,
                         extra={'gw_mac': gw_mac, 'GDDO': json.dumps(GDDO)})

            if GDDO['GCS'] is not SecureClient.SECURE_GCS_CONNECTED:
                logger.warn('gateway %s not connected, ignoring message' % gw_mac, extra={'gw_mac': gw_mac})

            # the GW name is submitted separately
            gw_name = [GWUDO for GWUDO in res['GWUDO'] if GWUDO['GMACID'] == gw_mac][0]['GN']
            gw_data = [GD for GD in res['GD'] if GD['GMACID'] == gw_mac][0]
            gw_serial = gw_data['GSN']

            gateway_created = False
            gateway_set = Gateway.objects.filter(external_id=gw_mac)
            vendor, _ = Vendor.objects.get_or_create(name=secure_vendor_name)
            if not gateway_set.exists():
                gateway = Gateway(external_id=gw_mac, site=site, vendor=vendor)
                gateway.save()
                gateway_created = True
            else:
                gateway = gateway_set.first()

            if not gateway.properties.filter(key='GN').exists():
                gateway.properties.create(key='GN', value=gw_name)
            if not gateway.properties.filter(key='GSN').exists():
                gateway.properties.create(key='GSN', value=gw_serial)

            if gateway_created:
                gateway.properties.create(key=SECURE_SERVER_NAME, value=self.secure_server_name)

            # Node does not exist for secure
            # on initial import all devices are on the same node
            # later, device can be moved to other nodes @todo support
            node, node_created = Node.objects.get_or_create(gateway=gateway, vendor=vendor)

            # import all device data
            for zone in GDDO['ZNDS']:
                zone_id = zone['ZID']
                zone_data = [zone for zone in gw_data['ZNS'] if zone['ZID'] == zone_id][0]

                # iterate over all device data
                for DDDO in zone['DDDO']:
                    dRefID = DDDO['DRefID']

                    device_data = [dev for dev in zone_data['DVS'] if dev['DRefID'] == dRefID][0]
                    device_type_str = ep_secure_importer.models.dtype_map[device_data['DTID']]
                    #             print('{}: {}'.format(dRefID,device_type))

                    # distinguish SSP302 and SIR321 by parameters
                    if device_type_str == ep_secure_importer.models.SecureDeviceType.RELAY:
                        instantaneous_power_parameters = [param for param in device_data['DPDO'] if
                                                          param['DPRefID'] == 102]
                        if any(instantaneous_power_parameters):
                            device_type_str = ep_secure_importer.models.SecureDeviceType.SIR321
                        else:
                            device_type_str = ep_secure_importer.models.SecureDeviceType.SSP302

                    device_type, created = DeviceType.objects.get_or_create(code=device_type_str)
                    if created:
                        if device_type_str in ep_secure_importer.models.devicetype_description_map:
                            device_type.description = ep_secure_importer.models.devicetype_description_map[
                                device_type_str]
                            device_type.save()
                        logger.info('Created DeviceType: {}'.format(device_type))

                    try:
                        device = Device.objects.get(external_id=dRefID, node__gateway=gateway)
                    except Device.DoesNotExist:
                        # use the factory method, because we want to have device parameters created as well
                        logger.info("Creating new device with external id %s" % dRefID)
                        device = Device(node=node, type=device_type, vendor=vendor, external_id=dRefID)
                        device.save()

                    SecureClient.store_device_state_from_DPDO(DDDO, device)

    @staticmethod
    def process_push_data(res):
        """
        Push data comes over the websocket.
        1.
        :return:
        """

        # import from all gateways
        GDDO = res['GDDO']
        gw_mac = GDDO['GMACID']
        logger.info("Processing push data from gateway %s" % gw_mac,
                    extra={'data': json.dumps(GDDO), 'gateway': gw_mac})
        gateway = Gateway.objects.get(external_id=gw_mac)

        # import all device data
        for zone in GDDO['ZNDS']:

            # iterate over all device data
            for DDDO in zone['DDDO']:
                dRefID = DDDO['DRefID']

                try:
                    device = Device.objects.get(external_id=dRefID, node__gateway=gateway)
                except Device.DoesNotExist as e:
                    logger.error(e)
                    continue

                SecureClient.store_device_state_from_DPDO(DDDO, device)

    @staticmethod
    def store_device_state_from_DPDO(DDDO, device):
        # iterate over all device parameters, create measurements
        # when a new device param is found, create a new model instance
        # do not duplicate

        try:
            device_parameter_map = ep_secure_importer.models.device_to_deviceparameter_type_map[device.type.code]

        except KeyError as e:
            logger.warn("Unhandled device type: {}".format(device.type.code))
            return

        for DPDO in DDDO['DPDO']:
            param_type_str = str(DPDO['DPRefID'])

            if param_type_str not in device_parameter_map:
                logger.info("Ignoring device parameter in push message: {}".format(param_type_str))
                continue

            parameter_type, created = DeviceParameterType.objects.get_or_create(code=param_type_str)
            if created:
                if param_type_str in ep_secure_importer.models.device_parameter_type_description_map:
                    parameter_type.description = ep_secure_importer.models.device_parameter_type_description_map[
                        param_type_str]
                    parameter_type.save()
                logger.info('Created new DP Type: {}'.format(parameter_type))

            try:
                SecureClient.store_device_state_info(DPDO, device, parameter_type)

            except DeviceParameter.DoesNotExist as e:
                logger.info('Creating new DP with type %s' % parameter_type)

                if param_type_str in ep_secure_importer.models.unit_map:
                    unit = ep_secure_importer.models.unit_map[param_type_str]
                else:
                    unit = None
                    logger.warn("Could not find unit mapping for new device parameter.")

                actions = ep_secure_importer.models.SecureDeviceParameterActions()
                actions.save()
                DeviceParameter(device=device, type=parameter_type, unit=unit, actions=actions).save()
                SecureClient.store_device_state_info(DPDO, device, parameter_type)

    @staticmethod
    def parse_value(DPDO):
        try:
            value = Decimal(DPDO['CV'])
        except:
            if DPDO['CV'] == 'True' or DPDO['CV'] == 'False':
                value = Decimal(bool(DPDO['CV']))
            else:
                logger.error('Could not parse value {} to Decimal'.format(DPDO['CV']))
                value = Decimal(0)
        return value

    @staticmethod
    def store_device_state_info(DPDO, device, param_type):
        device_parameter = DeviceParameter.objects.get(device=device, type=param_type)

        # @todo test if the correct measurement is found and if the LUT is correctly compared
        value = SecureClient.parse_value(DPDO)
        lut_str = DPDO['LUT']
        lut_dt = parse_datetime(lut_str)

        ts_loc = pytz.timezone('Europe/London').localize(lut_dt)
        lut_utc = ts_loc.astimezone(pytz.UTC)

        latest = device_parameter.measurements.latest()

        if latest:
            latest_ts = parse_datetime(latest['time'])

            if not lut_utc > latest_ts:
                logger.info(
                    "Ignoring old device parameter state (not changed from most recent value) [%s]" % device_parameter.id,
                    extra={'site': secure_site_name, 'device': device, 'type': device_parameter.type,
                           'current': value, 'device_parameter': device_parameter.id, 'time': lut_utc,
                           'gateway': device.node.gateway_id}
                )
                return

        trigger = SecureClient.get_trigger_source(device_parameter, value)

        logger.info(
            "Storing measurement value {} for device param {} of device {}".format(value,
                                                                                   device_parameter,
                                                                                   device),
            extra={'site': secure_site_name, 'device': device, 'type': device_parameter.type, 'current': value,
                   'trigger': trigger, 'device_parameter': device_parameter.id, 'time': lut_utc,
                   'gateway': device.node.gateway_id}
        )
        device_parameter.measurements.add(time=lut_utc, value=value, trigger=trigger)

    @staticmethod
    def store_device_state_change_request(device_param_id, target_value, source):
        logger.info('store_device_state_change_request from {}: device param {} to {}'.format(source, device_param_id,
                                                                                              target_value))
        key = "state_change_req/{}".format(device_param_id)
        value = "{target_value}/{source}".format(target_value=target_value, source=source)
        # never expire these automatically
        mc.set(key, value, 0)

    @staticmethod
    def get_trigger_source(device_param, current_value):
        """
        Heuristic to determine if the trigger source for an observed device state change was the
        schedule, an API request or a user.

        A scheduled and an API request both record state changes with their target values.
        If the target value is differnet to those, then we assume it was a change requested on the device.
        """
        key = "state_change_req/{}".format(device_param.id)
        if key in mc:
            value = mc[key]
            target_value, source = value.split("/")
            if Decimal(target_value) == current_value:
                return source
        return StateChangeEvent.ON_DEVICE

    @staticmethod
    def get_extra_headers(ak=None, ak_id=None, path=None, data_str=None):
        date_header = SecureClient.get_dateheader()
        extra_headers = {'DateHeader': date_header}

        if data_str:
            content_md5 = SecureClient.prepare_content_md5(data_str)
            extra_headers['Content-MD5'] = content_md5
            string_to_sign = '\n'.join(['POST', content_md5, date_header, str(ak_id), path.lower()])
        else:
            string_to_sign = '\n'.join(['GET', date_header, str(ak_id), path.lower()])

        digest = hmac.new(ak.encode('utf8'), msg=string_to_sign.encode('utf8'), digestmod=hashlib.sha1).digest()
        signature = base64.b64encode(digest)

        extra_headers['Authorization'] = 'SHS ' + str(ak_id) + ':' + signature.decode('ascii')

        return extra_headers

    @staticmethod
    def prepare_content_md5(content):
        content_md5 = hashlib.md5(content.encode('utf-8')).digest()
        signature = base64.b64encode(content_md5)
        return signature.decode("utf-8")

    @staticmethod
    def delete_auth_tokens(secure_server_name):
        logger.info("Deleting secure server login token from memcache")
        mc.delete('secure_ak_%s' % secure_server_name)

    @staticmethod
    def store_auth_keys(ak, ak_id, secure_server_name):
        # never expire these automatically
        mc.set('secure_ak_%s' % secure_server_name, ak, 0)
        mc.set('secure_ak_id_%s' % secure_server_name, ak_id, 0)

    @staticmethod
    def hash_password(password):
        m = hashlib.md5()
        m.update(password.encode("ascii"))
        md5_password = m.hexdigest()
        return md5_password

    @staticmethod
    def get_dateheader():
        # format yyyyMMddTHHmmssfffZ
        dateheader = datetime.datetime.now().strftime('%Y%m%dT%H%M%S%f%Z')[:-3] + 'Z'
        return dateheader

    @staticmethod
    def get_websocket_url(ak, ak_id, secure_server_name):
        server = 'ws://%s' % settings.SECURE_SERVERS[secure_server_name]['WSHOST']
        path = "/WebSocket/ConnectWebSocket".lower()

        date_time = SecureClient.get_dateheader()
        string_to_sign = '\n'.join(['GET', date_time, str(ak_id), path])

        digest = hmac.new(ak.encode('utf8'), msg=string_to_sign.encode('utf8'), digestmod=hashlib.sha1).digest()
        signature = base64.b64encode(digest).decode('ascii')

        connection_url = '{server}{path}?accessKeyID={AKID}&authorization={signature}&date={date_time}'.format(
            server=server,
            path=path,
            AKID=ak_id,
            signature=signature,
            date_time=date_time)

        return connection_url
