import logging
from decimal import Decimal

import amqpstorm
import simplejson as json
from celery import Task
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from ep.models import DeviceParameter, ScheduleDeviceParameterGroup, StateChangeEvent

__author__ = 'schien'

logger = logging.getLogger(__name__)


class ErrorLoggingTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error("CollectPrefectTask failed: %s" % einfo)


class IODICUS_AMQP_Task(Task):
    abstract = True
    _channel = None
    _connection = None

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error("IODICUS_AMQP_Task failed")
        logger.error(einfo)

    @property
    def channel(self):
        if self._channel is None:
            self._connection = amqpstorm.Connection(settings.IODICUS_MESSAGING_HOST,
                                                    settings.IODICUS_MESSAGING_USER,
                                                    settings.IODICUS_MESSAGING_PASSWORD,
                                                    port=settings.IODICUS_MESSAGING_PORT,
                                                    ssl=settings.IODICUS_MESSAGING_SSL)

            self._channel = self._connection.channel()

            self._channel.exchange.declare(exchange=settings.IODICUS_MESSAGING_EXCHANGE_NAME, exchange_type='fanout')
        return self._channel


@shared_task(base=IODICUS_AMQP_Task, bind=True)
def send_msg(self, json_payload):
    logger.debug('Publishing new message %s' % json_payload)

    self.channel.basic.publish(body=json_payload,
                               # body
                               routing_key='',  # routing key
                               exchange=settings.IODICUS_MESSAGING_EXCHANGE_NAME,
                               properties={
                                   'delivery_mode': 2,  # make message persistent
                                   'content_type': 'application/json',

                               })


@shared_task(base=ErrorLoggingTask)
def change_device_state(device_parameter_id: int, target_value: Decimal, trigger: str):
    """
    Complex interaction about device state change.
    @todo extract into single controller

    At present, the memcache stores the source of a change request request by schedule and EBE.
    If a change is observed, the new value is compared with the target value. If the target value is
    identical to that stored, it is assumed that was the trigger.

    If not, it is assumed the change was requested on the device.
    """
    device_parameter = DeviceParameter.objects.get(pk=device_parameter_id)

    latest = device_parameter.measurements.latest()
    message_dict = {'device_parameter': device_parameter.pk, 'current': latest['value'] if latest else None,
                    'type': device_parameter.type.code, 'intent': target_value, 'action': 'change_request',
                    'trigger': trigger, 'site': device_parameter.device.node.gateway.site.name,
                    'time': timezone.now().isoformat()}

    logger.info("Received change state request.".format(device_parameter.pk), extra=message_dict)

    # notify event subscribers

    if device_parameter.actions:
        message = json.dumps(message_dict)
        send_msg.subtask()(message)
        device_parameter.actions.change_device_state(device_parameter_id=device_parameter_id, target_value=target_value,
                                                     trigger=trigger)
    else:
        logger.info("Device parameter {} does not support change state requests.".format(device_parameter.pk),
                    extra=message_dict)


@shared_task
def health_log_task():
    logger.info("celery worker alive")


@shared_task(base=ErrorLoggingTask, bind=True)
def scheduled_device_state_change(self, device_group_id=None, target_value=None):
    device_group = ScheduleDeviceParameterGroup.objects.get(id=device_group_id)

    for device_param in device_group.device_parameters.all():
        logger.info('Scheduled device parameter [{}] change to value {}'.format(device_param, target_value))
        # now call the common change_device_state task

        change_device_state.subtask()(device_param.id, target_value, StateChangeEvent.SCHEDULE)
