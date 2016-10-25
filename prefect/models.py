from django.db import models
from ep.models import Unit, Device

__author__ = 'mitchell'


class PrefectDeviceParameterType(object):
    CURRENT_TEMP = 'TS'
    SETPOINT_TEMP = 'TH'
    PIR = 'PR'
    PREFECT_TEMPERATURE_ADJUSTMENT = 'TA'
    RELAY_ONE = 'R1'
    RELAY_TWO = 'R2'
    ENERGY_CONSUMPTION = 'EC'


class PrefectDeviceType(object):
    THERMOSTAT = 'TH'
    PIR = 'PR'
    RELAY = 'RL'

devicetype_description_map = {
    PrefectDeviceType.THERMOSTAT: 'Thermostat',
    PrefectDeviceType.PIR: 'PIR',
    PrefectDeviceType.RELAY: 'Prefect Relay',
}

device_to_deviceparameter_type_map = {
    PrefectDeviceType.THERMOSTAT: [PrefectDeviceParameterType.SETPOINT_TEMP, PrefectDeviceParameterType.CURRENT_TEMP],
    PrefectDeviceType.PIR: [PrefectDeviceParameterType.PIR],
    PrefectDeviceType.RELAY: [PrefectDeviceParameterType.RELAY_ONE, PrefectDeviceParameterType.RELAY_TWO,
                              PrefectDeviceParameterType.ENERGY_CONSUMPTION],
}

unit_map = {
    PrefectDeviceParameterType.CURRENT_TEMP: Unit.CELSIUS,
    PrefectDeviceParameterType.SETPOINT_TEMP: Unit.CELSIUS,
    PrefectDeviceParameterType.PIR: Unit.NO_UNIT,
    PrefectDeviceParameterType.RELAY_ONE: Unit.NO_UNIT,
    PrefectDeviceParameterType.RELAY_TWO: Unit.NO_UNIT,
    PrefectDeviceParameterType.ENERGY_CONSUMPTION: Unit.KWH
}

device_parameter_type_description_map = {
    PrefectDeviceParameterType.PIR: 'PIR',
    PrefectDeviceParameterType.CURRENT_TEMP: 'current_temperature',
    PrefectDeviceParameterType.SETPOINT_TEMP: 'temperature_setpoint',
    PrefectDeviceParameterType.RELAY_ONE: 'relay_1_state',
    PrefectDeviceParameterType.RELAY_TWO: 'relay_2_state',
    PrefectDeviceParameterType.ENERGY_CONSUMPTION: 'calculated_energy_consumption',
}


class PrefectDeviceParameterConfiguration(models.Model):
    device = models.ForeignKey(Device, related_name='configuration')
    power_consumption = models.DecimalField(null=False, decimal_places=2, max_digits=7)
    line = models.CharField(max_length=2, null=False)

    def __str__(self):
        return "(%s, Line %s)" % (self.power_consumption, self.line)

    class Meta:
        verbose_name = 'Prefect Device Configuration'
