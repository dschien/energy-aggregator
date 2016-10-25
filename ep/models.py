import logging
from decimal import Decimal
from datetime import datetime

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

import ep
import requests
import simplejson as json
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from influxdb import InfluxDBClient
from weekday_field.fields import WeekdayField

logger = logging.getLogger(__name__)


class BaseEntity(models.Model):
    class Meta:
        abstract = True

    def get_content_type(self):
        return ContentType.objects.get_for_model(self).id


class Unit(object):
    CELSIUS = 'C'
    WATTS = 'W'
    NO_UNIT = 'N'
    PERCENT = '%'
    BOOL = 'B'
    SECONDS = 'S'
    KWH = 'K'


class Site(BaseEntity):
    name = models.CharField(max_length=50, default='site', null=False, unique=True)

    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    actions = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return self.name


class SiteProperty(models.Model):
    site = models.ForeignKey(Site, related_name='properties')
    key = models.CharField(max_length=50, null=True)
    value = models.CharField(max_length=200, null=True)

    def __str__(self):
        return "%s: %s" % (self.key, self.value)


class Vendor(models.Model):
    name = models.CharField(max_length=80, null=False)

    def __str__(self):
        return "{name}".format(name=self.name)


class Gateway(BaseEntity):
    site = models.ForeignKey(Site, related_name='gateways')
    vendor = models.ForeignKey(Vendor, related_name='gateways')
    external_id = models.CharField(max_length=200, blank=True, null=True, default='default', unique=True)

    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    actions = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return "{site}: {id}".format(site=self.site, id=self.external_id)


SECURE_SERVER_NAME = 'secure-server-name'


class GatewayProperty(models.Model):
    gateway = models.ForeignKey(Gateway, related_name='properties')
    key = models.CharField(max_length=50, null=True)
    value = models.CharField(max_length=200, null=True)

    def __str__(self):
        return "%s: %s" % (self.key, self.value)


class Node(BaseEntity):
    gateway = models.ForeignKey(Gateway, related_name='nodes')
    vendor = models.ForeignKey(Vendor, related_name='nodes')
    space_name = models.CharField(max_length=100, null=True)
    floor = models.CharField(max_length=10, null=True)
    building = models.CharField(max_length=50, null=True)
    external_id = models.CharField(max_length=200, null=True, default='default', db_index=True)

    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    actions = GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = ('gateway', 'external_id',)

    def __str__(self):
        result = "[{id}]: {external_id}".format(id=self.id, external_id=self.external_id)
        if self.space_name is not None:
            result += " \"{}\"".format(self.space_name)
        return result


class NodeProperty(models.Model):
    node = models.ForeignKey(Node, related_name='properties')
    key = models.CharField(max_length=50, null=True)
    value = models.CharField(max_length=200, null=True)

    def __str__(self):
        return "%s: %s" % (self.key, self.value)


class DeviceType(models.Model):
    code = models.CharField(max_length=50, null=False, db_index=True)
    description = models.CharField(max_length=100, null=True)

    def __str__(self):
        result = "{}".format(self.code)
        if self.description is not None:
            result += " {}".format(self.description)
        return result


class Device(BaseEntity):
    node = models.ForeignKey(Node, related_name='devices')
    vendor = models.ForeignKey(Vendor, related_name='devices')
    type = models.ForeignKey(DeviceType, related_name='devices')
    name = models.CharField(max_length=50, null=True)
    external_id = models.CharField(max_length=200, null=True, db_index=True)
    precedence = models.IntegerField(null=True, default=50)

    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    actions = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        result = "[{id}]".format(id=self.id)

        if self.type is not None:
            result += " {type}".format(type=self.type)

        if self.name is not None:
            result += " {name}".format(name=self.name)
        else:
            if self.external_id is not None:
                result += " {external_id}".format(external_id=self.external_id)

        return result

    @property
    def last_update_time(self):
        """
        Synthesise this from the DP with the last update time
        :return:
        """
        lut = None
        for dp in self.parameters.all():
            latest = dp.measurements.latest()
            if latest:
                latest_ts = parse_datetime(latest['time'])
                if not lut or lut < latest_ts:
                    lut = latest_ts
        return lut.strftime('%x %X')


class DeviceParameterType(models.Model):
    code = models.CharField(max_length=80, null=False, db_index=True)
    description = models.CharField(max_length=100, null=True)

    def __str__(self):
        return "{} {}".format(self.code, self.description)


class DeviceParameter(BaseEntity):
    device = models.ForeignKey(Device, related_name='parameters')
    type = models.ForeignKey(DeviceParameterType, related_name='device_parameters')
    unit = models.CharField(max_length=80, null=True)

    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    actions = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        result = "[{id}] (device {device})".format(id=self.id, device=self.device.external_id)
        if self.type is not None:
            result += "[{type}]".format(type=self.type)
        return result

    @property
    def measurements(self):
        return DPMeasurements(device_parameter=self)

    @property
    def last_update_time(self):
        latest = self.measurements.latest()
        if latest:
            latest_ts = parse_datetime(latest['time'])
            return latest_ts.strftime('%x %X')


class StateChangeEvent(models.Model):
    device_property = models.ForeignKey(DeviceParameter)

    ON_DEVICE = 'OD'
    EBE = 'EB'
    API = 'AP'
    SCHEDULE = 'SC'

    TRIGGER_CHOICES = (
        (ON_DEVICE, 'C'),
        (SCHEDULE, 'A'),
        (EBE, 'E'),

    )
    trigger = models.CharField(max_length=2,
                               choices=TRIGGER_CHOICES)

    date_time = models.DateTimeField()

    previous_value = models.DecimalField(max_digits=7, decimal_places=2, null=True)
    new_value = models.DecimalField(max_digits=7, decimal_places=2, null=True)

    class Meta:
        ordering = ['-date_time']
        get_latest_by = "date_time"


class Tariff(models.Model):
    name = models.CharField(max_length=50, null=True)
    enabled = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Band(models.Model):
    tariff = models.ForeignKey(Tariff, related_name='bands')

    valid_from = models.DateField()
    valid_to = models.DateField()

    # @todo there is a breaking dependency on SubFieldBase which was removed in django 1.10.
    # @todo either replace this or fix this
    weekdays = WeekdayField()

    start_time = models.TimeField()
    end_time = models.TimeField()

    name = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.name if self.name else "{} - {}".format(self.start_time, self.end_time)


class TariffBandProperty(models.Model):
    band = models.ForeignKey(Band, related_name='properties')
    key = models.CharField(max_length=50, null=True)
    value = models.CharField(max_length=200, null=True)

    def __str__(self):
        return "%s: %s" % (self.key, self.value)


class ScheduleDeviceParameterGroup(models.Model):
    """
    A schedule is implemented with :func:`djcelery.PeriodicTasks` and a :func:`scheduled_device_state_change` task.
    All device parameters in a ScheduleDeviceParameterGroup will have their values set to the target values defined in
    the PeriodicTask.

    E.g. if there are devices A and B in the schedule and the schedule has two SSC's X and Y with
    X.scheduled_time = Monday 9:00 am with X.target_value = 80 and
    Y.scheduled_time = Monday 16:00 am with Y.target_value = 10

    then A and B will change their target values to 80 on Monday morning and back to 10 on Monday afternoon.
    """
    device_parameters = models.ManyToManyField(DeviceParameter,
                                               related_name='schedule',
                                               # @todo fix this
                                               # limit_choices_to={'device__node__gateway__site': Site.objects.get(
                                               #     name=secure_site_name).id}
                                               )

    # name = models.CharField(max_length=50, null=True)

    def __str__(self):
        return "[{id}] {name}".format(id=self.id, name=self.name)


session = requests.Session()


class TSMeasurements(object):
    MEASUREMENT_NAME = 'TS'
    DEFAULT_TAG_NAME = None
    DEFAULT_TAG_VALUE = None

    def __init__(self, measurement_name, tag_name=None, tag_value=None):
        self.MEASUREMENT_NAME = measurement_name
        self.DEFAULT_TAG_NAME = tag_name
        self.DEFAULT_TAG_VALUE = tag_value

        self.client = InfluxDBClient(settings.INFLUXDB_HOST, settings.INFLUXDB_PORT, settings.INFLUXDB_USER,
                                     settings.INFLUXDB_PASSWORD, settings.INFLUX_DB_NAME, session=session)

    @staticmethod
    def time():
        return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    def add(self, time=None, value=None, tags=None):
        """
        :time: a datetime
        :value: a measurement value
        :tags: a dictionary of additional tags to include
        """

        if time is None:
            time = self.time()

        if type(time) is datetime:
            time = time.strftime('%Y-%m-%dT%H:%M:%SZ')

        json_body = [
            {
                "measurement": "{}".format(self.MEASUREMENT_NAME),
                "tags": tags,
                "time": time,
                "fields": {
                    "value": float(value)
                }
            }
        ]

        logger.debug("Writing to TS DB", extra=json_body[0])
        self.client.write_points(json_body)

    def count(self, tag_name=None, tag_value=None):
        tag_name = tag_name or self.DEFAULT_TAG_NAME
        tag_value = tag_value or self.DEFAULT_TAG_VALUE

        if tag_name and tag_value:
            query = "SELECT count(value) FROM {measurement_name} WHERE {tag_name} = '{tag_value}'".format(
                measurement_name=self.MEASUREMENT_NAME, tag_value=int(tag_value),
                tag_name=tag_name)
        else:
            query = "SELECT count(value) FROM {}".format(self.MEASUREMENT_NAME)
        result = list(self.client.query(query).get_points())

        if result:
            return result[0]['count']
        else:
            return 0

    def exists(self, tag_name=None, tag_value=None):
        """
        Returns true if measurement exists
        :param tag_name:
        :param tag_value:
        :return:
        """
        tag_name = tag_name or self.DEFAULT_TAG_NAME
        tag_value = tag_value or self.DEFAULT_TAG_VALUE

        if tag_name and tag_value:
            query = "SELECT count(value) FROM {measurement_name} WHERE {tag_name} = '{tag_value}'".format(
                measurement_name=self.MEASUREMENT_NAME, tag_value=int(tag_value),
                tag_name=tag_name)
        else:
            query = "SELECT count(value) FROM {}".format(self.MEASUREMENT_NAME)
        result = list(self.client.query(query).get_points())

        if result and result[0]['count'] > 0:
            return True
        else:
            return False

    def latest(self, tag_name=None, tag_value=None):
        tag_name = tag_name or self.DEFAULT_TAG_NAME
        tag_value = tag_value or self.DEFAULT_TAG_VALUE

        if tag_name and tag_value:
            query = "SELECT * FROM {measurement_name} WHERE {tag_name} = '{tag_value}' order by time desc limit 1".format(
                measurement_name=self.MEASUREMENT_NAME, tag_value=int(tag_value),
                tag_name=tag_name)
            result = list(self.client.query(query).get_points())
            if result:
                latest = result[0]
                # populate regular value key
                latest['value'] = Decimal(str(latest['value']))
                return latest
        return None

    def all(self, tag_name=None, tag_value=None, start_date=None):
        """
        :start_date: an UTC datetime
        @todo cast return values to Decimal for internal consistency
        """
        tag_name = tag_name or self.DEFAULT_TAG_NAME
        tag_value = tag_value or self.DEFAULT_TAG_VALUE

        query = "SELECT value FROM {}".format(self.MEASUREMENT_NAME)

        with_where = False
        if tag_name and tag_value:
            with_where = True
            query += " WHERE {tag_name}='{tag_value}'".format(
                tag_value=int(tag_value), tag_name=tag_name)

        if start_date:
            if with_where:
                query += " AND "
            else:
                query += " WHERE "
            query += "time > '{}'".format(start_date.replace(tzinfo=timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f"))
        query += " order by time desc"
        result = self.client.query(query)

        return result.get_points()


class DPMeasurements(TSMeasurements):
    device_parameter = None
    INFLUX_DEVICE_PARAMETER_MEASUREMENT_NAME = 'device_parameters%s' % settings.INFLUX_MEASUREMENT_SUFFIX
    TAG = 'dp'

    def __init__(self, device_parameter=None):
        self.device_parameter = device_parameter
        super().__init__(self.INFLUX_DEVICE_PARAMETER_MEASUREMENT_NAME, self.TAG, self.device_parameter.id)

    def add(self, time=None, value=None, trigger=StateChangeEvent.ON_DEVICE, extra_tags=None):
        tags = {
            self.TAG: "{}".format(int(self.device_parameter.id)),
            "type": "{}".format(self.device_parameter.type.code),
            "trigger": trigger
        }

        if extra_tags is not None:
            tags.update(extra_tags)

        latest = self.latest()
        super().add(time, value, tags)

        # @todo check with Critical...
        latest_value = latest['value'] if latest else None
        if not latest or latest_value != value:
            site = self.device_parameter.device.node.gateway.site.name
            logger.debug('Device parameter state change',
                         extra={'device': self.device_parameter.device,
                                'device_parameter': self.device_parameter.id,
                                'site': site,
                                'type': self.device_parameter.device.type,
                                'previous': latest_value,
                                'current': value, 'action': 'change_record'})

            message = {'device_parameter': self.device_parameter.id, 'previous': latest_value,
                       'type': self.device_parameter.type.code, 'current': value,
                       'action': 'change_record', 'trigger': trigger, 'site': site, 'time': time.isoformat()}
            logger.info(
                "Broadcasting measured device state change for device parameter {}".format(self.device_parameter.id),
                extra=message)

            ep.tasks.send_msg.delay(json.dumps(message))


class GCSMeasurements(TSMeasurements):
    INFLUX_GATEWAY_MEASUREMENT_NAME = 'gateway_online%s' % settings.INFLUX_MEASUREMENT_SUFFIX
    TAG = 'external_id'
    gateway = None

    def __init__(self, gateway=None):
        self.gateway = gateway
        super().__init__(self.INFLUX_GATEWAY_MEASUREMENT_NAME, self.TAG, self.gateway.external_id)

    def add(self, time, value):
        tags = {
            self.TAG: "{}".format(int(self.gateway.external_id))
        }
        logger.debug('About to write GCS to TS DB')
        super().add(time, value, tags)
