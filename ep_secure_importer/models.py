import logging

from ep.models import Unit, DeviceParameter, SECURE_SERVER_NAME
from django.db import models

from ep_secure_importer.controllers.secure_client import SecureClient, secure_vendor_name

__author__ = 'mitchell'
logger = logging.getLogger(__name__)


class SecureDeviceParameterActions(models.Model):
    @staticmethod
    def change_device_state(device_parameter_id=None, target_value=None, trigger=None):
        logger.info("Processing device parameter change request", extra={"device_param": device_parameter_id})
        SecureClient.store_device_state_change_request(device_parameter_id, target_value, trigger)

        device_parameter = DeviceParameter.objects.get(pk=device_parameter_id)
        logger.info("Found device parameter", extra={"device_param": device_parameter.pk})
        gateway = device_parameter.device.node.gateway
        if gateway.vendor.name == secure_vendor_name:
            logger.info("Requesting device parameter change", extra={"device_param": device_parameter.pk})
            secure_server_name = gateway.properties.filter(key=SECURE_SERVER_NAME).get().value
            SecureClient(secure_server_name).change_secure_device_state(device_parameter, target_value)
        else:
            logger.warn("Secure change_device_state action called for non-secure device",
                        extra={"device_param": device_parameter.pk})


class SecureDeviceType(object):
    RELAY = 'RL'
    SRT321 = 'ST'
    SIR321 = 'SR'
    SSP302 = 'SP'
    SECURE_MOTION_SENSOR = 'SM'


class SecureDeviceParameterType(object):
    # Prefect fields
    BATTERY_LEVEL = '101'
    SCHEDULE_ID_ACTIVE = '102'
    SCHEDULE_OVERRIDES_SUPPORTED = '107'

    CURRENTLY_IGNORED_FIELD = '111'
    WAKE_UP_FREQUENCY = '112'
    WAKE_UP_NODE = '113'
    MOTION_DETECTED = '115'

    TARGET_TEMPERATURE = '201'
    MEASURED_TEMPERATURE = '202'
    HOME_TEMPERATURE = '211'
    AWAY_TEMPERATURE = '212'

    MEASURED_TEMPERATURE_REPORT_DELTA = '214'
    ASSOCIATED_SWITCH = '216'
    CALL_FOR_HEAT = '217'

    BINARY_SWITCH = '301'
    ACCUMULATED_ENERGY = '304'
    INSTANTANEOUS_POWER = '305'
    ACCUMULATED_ENERGY_REPORTING_DELTA = '307'
    INSTANTANEOUS_POWER_REPORTING_DELTA = '306'
    INSTANTANEOUS_POWER_REPORTING_FREQUENCY = '308'
    ACCUMULATED_ENERGY_REPORTING_FREQUENCY = '309'


device_parameter_type_description_map = {
    SecureDeviceParameterType.BATTERY_LEVEL: 'battery_level',
    SecureDeviceParameterType.SCHEDULE_ID_ACTIVE: 'schedule_id_active',
    SecureDeviceParameterType.SCHEDULE_OVERRIDES_SUPPORTED: 'schedule_overrides_supported',
    SecureDeviceParameterType.WAKE_UP_FREQUENCY: 'wake_up_frequency',
    SecureDeviceParameterType.WAKE_UP_NODE: 'wake_up_node',
    SecureDeviceParameterType.MOTION_DETECTED: 'motion_detected',
    SecureDeviceParameterType.TARGET_TEMPERATURE: 'target_temperature',
    SecureDeviceParameterType.MEASURED_TEMPERATURE: 'measured_temperature',
    SecureDeviceParameterType.HOME_TEMPERATURE: 'home_temperature',
    SecureDeviceParameterType.AWAY_TEMPERATURE: 'away_temperature',
    SecureDeviceParameterType.CALL_FOR_HEAT: 'call_for_heat',
    SecureDeviceParameterType.MEASURED_TEMPERATURE_REPORT_DELTA: 'measured_temperature_report_delta',
    SecureDeviceParameterType.ASSOCIATED_SWITCH: 'associated_switch',
    SecureDeviceParameterType.BINARY_SWITCH: 'binary_switch',
    SecureDeviceParameterType.ACCUMULATED_ENERGY: 'accumulated_energy',
    SecureDeviceParameterType.INSTANTANEOUS_POWER: 'instantaneous_power',
    SecureDeviceParameterType.ACCUMULATED_ENERGY_REPORTING_DELTA: 'accumulated_energy_reporting_delta',
    SecureDeviceParameterType.INSTANTANEOUS_POWER_REPORTING_DELTA: 'instantaneous_power_reporting_delta',
    SecureDeviceParameterType.INSTANTANEOUS_POWER_REPORTING_FREQUENCY: 'instantaneous_power_reporting_frequency',
    SecureDeviceParameterType.ACCUMULATED_ENERGY_REPORTING_FREQUENCY: 'accumulated_energy_reporting_frequency'
}

unit_map = {
    SecureDeviceParameterType.MOTION_DETECTED: Unit.NO_UNIT,
    SecureDeviceParameterType.BATTERY_LEVEL: Unit.PERCENT,
    SecureDeviceParameterType.SCHEDULE_ID_ACTIVE: Unit.NO_UNIT,
    SecureDeviceParameterType.SCHEDULE_OVERRIDES_SUPPORTED: Unit.BOOL,
    SecureDeviceParameterType.WAKE_UP_FREQUENCY: Unit.SECONDS,
    SecureDeviceParameterType.WAKE_UP_NODE: Unit.NO_UNIT,
    SecureDeviceParameterType.TARGET_TEMPERATURE: Unit.CELSIUS,
    SecureDeviceParameterType.MEASURED_TEMPERATURE: Unit.CELSIUS,
    SecureDeviceParameterType.HOME_TEMPERATURE: Unit.CELSIUS,
    SecureDeviceParameterType.AWAY_TEMPERATURE: Unit.CELSIUS,
    SecureDeviceParameterType.CALL_FOR_HEAT: Unit.BOOL,
    SecureDeviceParameterType.MEASURED_TEMPERATURE_REPORT_DELTA: Unit.CELSIUS,
    SecureDeviceParameterType.ASSOCIATED_SWITCH: Unit.NO_UNIT,
    SecureDeviceParameterType.BINARY_SWITCH: Unit.NO_UNIT,
    SecureDeviceParameterType.ACCUMULATED_ENERGY: Unit.KWH,
    SecureDeviceParameterType.INSTANTANEOUS_POWER: Unit.WATTS,
    SecureDeviceParameterType.ACCUMULATED_ENERGY_REPORTING_DELTA: Unit.KWH,
    SecureDeviceParameterType.INSTANTANEOUS_POWER_REPORTING_DELTA: Unit.WATTS,
    SecureDeviceParameterType.INSTANTANEOUS_POWER_REPORTING_FREQUENCY: Unit.SECONDS,
    SecureDeviceParameterType.ACCUMULATED_ENERGY_REPORTING_FREQUENCY: Unit.SECONDS,
}

device_to_deviceparameter_type_map = {
    SecureDeviceType.RELAY: [],

    SecureDeviceType.SRT321: [SecureDeviceParameterType.BATTERY_LEVEL, SecureDeviceParameterType.WAKE_UP_FREQUENCY,
                              SecureDeviceParameterType.WAKE_UP_NODE, SecureDeviceParameterType.TARGET_TEMPERATURE,
                              SecureDeviceParameterType.MEASURED_TEMPERATURE,
                              SecureDeviceParameterType.HOME_TEMPERATURE,
                              SecureDeviceParameterType.AWAY_TEMPERATURE, SecureDeviceParameterType.CALL_FOR_HEAT,
                              SecureDeviceParameterType.MEASURED_TEMPERATURE_REPORT_DELTA,
                              SecureDeviceParameterType.ASSOCIATED_SWITCH],

    SecureDeviceType.SIR321: [SecureDeviceParameterType.BINARY_SWITCH, SecureDeviceParameterType.SCHEDULE_ID_ACTIVE,
                              SecureDeviceParameterType.SCHEDULE_OVERRIDES_SUPPORTED],

    SecureDeviceType.SSP302: [SecureDeviceParameterType.SCHEDULE_ID_ACTIVE,
                              SecureDeviceParameterType.SCHEDULE_OVERRIDES_SUPPORTED,
                              SecureDeviceParameterType.BINARY_SWITCH, SecureDeviceParameterType.ACCUMULATED_ENERGY,
                              SecureDeviceParameterType.INSTANTANEOUS_POWER,
                              SecureDeviceParameterType.INSTANTANEOUS_POWER_REPORTING_DELTA,
                              SecureDeviceParameterType.ACCUMULATED_ENERGY_REPORTING_DELTA,
                              SecureDeviceParameterType.INSTANTANEOUS_POWER_REPORTING_FREQUENCY,
                              SecureDeviceParameterType.ACCUMULATED_ENERGY_REPORTING_FREQUENCY],

    SecureDeviceType.SECURE_MOTION_SENSOR: [SecureDeviceParameterType.BATTERY_LEVEL,
                                            SecureDeviceParameterType.WAKE_UP_FREQUENCY,
                                            SecureDeviceParameterType.WAKE_UP_NODE,
                                            SecureDeviceParameterType.MEASURED_TEMPERATURE,
                                            SecureDeviceParameterType.MOTION_DETECTED]
}

devicetype_description_map = {
    SecureDeviceType.RELAY: 'Relay',
    SecureDeviceType.SIR321: 'SIR321 Relay',
    SecureDeviceType.SSP302: 'SSP302 Relay',
    SecureDeviceType.SECURE_MOTION_SENSOR: 'Secure Motion Sensor'
}

dtype_map = {
    2: SecureDeviceType.SRT321,
    4: SecureDeviceType.RELAY,
    8: SecureDeviceType.SECURE_MOTION_SENSOR
}
