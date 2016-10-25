import datetime
import json
import logging

from django.contrib.auth.models import Group
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from djcelery.models import PeriodicTask
from rest_framework import mixins
from rest_framework import permissions
from rest_framework import status, generics
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ep.models import Site, Node, DeviceParameter, Gateway, Tariff, Device, StateChangeEvent
from ep.serializers import SiteSerializer, NodeSerializer, DeviceStateMeasurementSerializer, DeviceParameterSerializer, \
    TariffSerializer, GatewaySerializer, DeviceSerializer
from ep.tasks import change_device_state

__author__ = 'schien'

logger = logging.getLogger(__name__)

# Name for the groups permitted to access API
uob_estates_group = 'uob_estates'
ebe_group = 'EBE'


def is_in_group(user, group_name):
    """
    Takes a user and a group name, and returns `True` if the user is in that group.
    """
    return Group.objects.get(name=group_name).user_set.filter(id=user.id).exists()


class HasGroupPermission(permissions.BasePermission):
    """
    Ensure user is in required groups.
    """

    def has_permission(self, request, view):
        # Get a mapping of methods -> required group.
        required_groups_mapping = getattr(view, 'required_groups', {})

        # Determine the required groups for this particular request method.
        required_groups = required_groups_mapping.get(request.method, [])

        # Return True if the user has all the required groups.
        return all([is_in_group(request.user, group_name) for group_name in required_groups])


class MeasurementList(mixins.ListModelMixin, generics.GenericAPIView):
    """
    Returns a list of all measurements for a given DeviceParameter within a duration.

    Parameters:

    - device_parameter_id (int): id of the device parameter to get the measurements for
    - query param `start_date` (ISO String, e.g. `2016-02-10T12:10:26Z` ), optional:
        start date of the duration. Default 30 days from today.

    Returns:

    - List of measurements as `time`, `value` pairs

    Example:

        [
          {
            time: "2016-05-18T14:46:52.950287872Z",
            value: 0
          },
          {
            time: "2016-05-18T14:46:50.943067904Z",
            value: 255
          },
        ]

    """

    serializer_class = DeviceStateMeasurementSerializer
    permission_classes = [HasGroupPermission]

    required_groups = {
        'GET': [uob_estates_group],
    }

    def get_queryset(self):
        """
        Return a list of measurements for a particular device
        :return:
        """
        param_id = self.kwargs['device_parameter_id']
        # start_date is an ISO String. I.e. "2016-02-10T12:10:26.213186Z"
        # @todo test
        start_datetime_param = self.request.query_params.get('start_date',
                                                             (timezone.now() - datetime.timedelta(days=30)).isoformat())
        start_date = parse_datetime(start_datetime_param)

        device_param = DeviceParameter.objects.get(id=param_id)

        return device_param.measurements.all(start_date=start_date)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class MeasurementsLatest(generics.RetrieveAPIView):
    """
    Returns the latest measurement for a DeviceParameter.


    Parameters:

    - device_parameter_id (int): id of the device parameter to get the measurements for

    Returns:

    - measurements as `time`, `value` pair

    Example:

        {
            time: "2016-05-18T14:46:52.950287872Z",
            value: 0
          },

    """

    serializer_class = DeviceStateMeasurementSerializer
    permission_classes = [HasGroupPermission]

    required_groups = {
        'GET': [uob_estates_group],
    }

    def get_object(self):
        """
        Return a list of measurements for a particular device
        :return:
        """
        param_id = self.kwargs['pk']
        device_param = DeviceParameter.objects.get(id=param_id)

        latest = device_param.measurements.latest()
        if not latest:
            raise Http404('No measurements found for device parameter %s.' % param_id)
        return latest


class NodeList(mixins.ListModelMixin,
               generics.GenericAPIView):
    """
    Returns a list of all nodes ids.


    Parameters:

    - pk (int), optional: id of a site to get the nodes for, by default all node ids will be returned

    Returns:

    - list of nodes ids

    Example:

           [
              {
                id: 61
              },
              {
                id: 62
              },
              {
                id: 613
              },
              {
                id: 614
              }
            ]


    """
    serializer_class = NodeSerializer
    permission_classes = [HasGroupPermission]

    required_groups = {
        'GET': [uob_estates_group],
        'POST': [uob_estates_group],
    }

    def get_queryset(self):
        """
        Return a list of measurements for a particular device
        :return:
        """
        if 'pk' in self.kwargs:
            site = Site.objects.get(pk=self.kwargs['pk'])
            return Node.objects.filter(gateway__site=site)
        else:
            return Node.objects.all()

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class DeviceList(mixins.ListModelMixin,
                 generics.GenericAPIView):
    """
    Returns details of all devices in a site.

    Parameters:

    - pk (int): id of a site to get the devices for

    Returns:

    - list of device details

    Example:

        {
          id: 181,
          type_name: "SECURE_MOTION_SENSOR",
          name: null,
          type: "SM",
          site_name: "secure_testsite",
          site_id: "3",
          gateway: "4",
          node: "62",
          device_parameters: [
            {
              id: 4323,
              type: "115",
              type_name: "115"
            },
            {
              id: 241,
              type: "101",
              type_name: "BATTERY_LEVEL"
            },
            {
              id: 242,
              type: "112",
              type_name: "wake_up_frequency"
            },
            {
              id: 243,
              type: "113",
              type_name: "wake_up_node"
            },
            {
              id: 244,
              type: "202",
              type_name: "measured_temperature"
            }
          ],
          precedence: 50
        },


    """
    serializer_class = DeviceSerializer
    permission_classes = [HasGroupPermission]

    required_groups = {
        'GET': [uob_estates_group],
        'POST': [uob_estates_group],
    }

    def get_queryset(self):
        """
        Return a list of measurements for a particular device
        :return:
        """
        if 'pk' in self.kwargs:
            site = Site.objects.get(pk=self.kwargs['pk'])
            return Device.objects.filter(node__gateway__site=site)
        else:
            return Device.objects.all()

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class DeviceDetails(generics.RetrieveAPIView):
    """
    Returns details of a device.

    Parameters:

    - pk (int): id of a device to get details for

    Returns:

    - Device details

    Example:

          {
            id: 181,
            type_name: "SECURE_MOTION_SENSOR",
            name: null,
            type: "SM",
            site_name: "secure_testsite",
            site_id: "3",
            gateway: "4",
            node: "62",
            device_parameters: [
              {
                id: 4323,
                type: "115",
                type_name: "115"
              },
              {
                id: 241,
                type: "101",
                type_name: "BATTERY_LEVEL"
              },
              {
                id: 242,
                type: "112",
                type_name: "wake_up_frequency"
              },
              {
                id: 243,
                type: "113",
                type_name: "wake_up_node"
              },
              {
                id: 244,
                type: "202",
                type_name: "measured_temperature"
              }
            ],
            precedence: 50
          }

    """
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [HasGroupPermission]

    required_groups = {
        'GET': [uob_estates_group],
        'POST': [uob_estates_group],
    }


class SiteList(mixins.ListModelMixin,
               generics.GenericAPIView):
    """
    Returns a list of all registered sites.

    Returns:

    - list of site ids

    Example:

           [
              {
                name: "badock",
                id: 1
              },
              {
                name: "goldney",
                id: 2
              },
              {
                name: "secure_testsite",
                id: 3
              }
            ]
    """
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    permission_classes = [HasGroupPermission]

    required_groups = {
        'GET': [uob_estates_group],
        'POST': [uob_estates_group],
    }

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class GatewayList(mixins.ListModelMixin,
                  generics.GenericAPIView):
    """
    Returns a list of all gateways for a site.

    Returns:

    - list of gateway ids

    Example:

           [
              {
                external_id: "3",
                id: 3
              },
              {
                external_id: "46477239136298",
                id: 4
              },
              {
                external_id: "46477239136514",
                id: 5
              },
              {
                external_id: "46477239136516",
                id: 6
              }
            ]
    """

    serializer_class = GatewaySerializer
    permission_classes = [HasGroupPermission]

    required_groups = {
        'GET': [uob_estates_group],
        'POST': [uob_estates_group],
    }

    def get_queryset(self):
        return Gateway.objects.filter(site=self.kwargs['pk'])

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class TariffList(mixins.ListModelMixin,
                 generics.GenericAPIView):
    """
    Returns a list of all known tariffs.

    Example:

        {
            id: 1,
            bands: [
              {
                valid_from: "2016-01-01",
                valid_to: "2017-12-31",
                weekdays: "0,1,2,3,4,5,6",
                start_time: "00:00:00",
                end_time: "23:59:59",
                properties: [
                  {
                    key: "cost_gbp_kwh",
                    value: "0.1"
                  },
                  {
                    key: "duos",
                    value: "False"
                  },
                  {
                    key: "triad",
                    value: "False"
                  }
                ]
              }
            ],
            name: "default",
            enabled: true
          },
    """
    queryset = Tariff.objects.all()
    serializer_class = TariffSerializer
    permission_classes = [HasGroupPermission]

    required_groups = {
        'GET': [uob_estates_group],
        'POST': [uob_estates_group],
    }

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class SiteDetailsView(generics.RetrieveAPIView):
    """
    Returns details of a single site.

    Parameters:

    - site_id (int): id of a site to get details for


    Returns:

    - details of site

    Example:

            {
                name: "badock",
                id: 1
              },
    """
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    permission_classes = [HasGroupPermission]

    required_groups = {
        'GET': [uob_estates_group],
        'POST': [uob_estates_group],
    }


class TariffDetailsView(generics.RetrieveAPIView):
    """
    Returns details for a single tariff.

    Example:

        {
            id: 1,
            bands: [
              {
                valid_from: "2016-01-01",
                valid_to: "2017-12-31",
                weekdays: "0,1,2,3,4,5,6",
                start_time: "00:00:00",
                end_time: "23:59:59",
                properties: [
                  {
                    key: "cost_gbp_kwh",
                    value: "0.1"
                  },
                  {
                    key: "duos",
                    value: "False"
                  },
                  {
                    key: "triad",
                    value: "False"
                  }
                ]
              }
            ],
            name: "default",
            enabled: true
          },
    """
    queryset = Tariff.objects.all()
    serializer_class = TariffSerializer
    permission_classes = [HasGroupPermission]

    required_groups = {
        'GET': [uob_estates_group],
        'POST': [uob_estates_group],
    }


class DeviceParameterDetailsView(generics.RetrieveUpdateAPIView):
    """
    Set a value for a DeviceParameter with HTTP PUT or PATCH.

    Parameters:

    - pk (int): id of DeviceParameter to change
    - post data: json object with target value to change the device parameter to

    Returns:

    - HTTP 200 in case of success

    Example

        post data {"target_value":255}

    """
    permission_classes = [HasGroupPermission]

    required_groups = {
        'PUT': [uob_estates_group],
        'PATCH': [uob_estates_group],
    }
    queryset = DeviceParameter.objects.all()
    serializer_class = DeviceParameterSerializer

    def request_device_state_change(self, request):
        device_parameter = self.get_object()

        if not device_parameter.actions:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED,
                            data={"message": "Device parameter does not support change state requests"})
        value = request.data['target_value']

        trigger = StateChangeEvent.API
        if is_in_group(request.user, ebe_group):
            trigger = StateChangeEvent.EBE

        change_device_state.delay(device_parameter.id, value, trigger)

        return Response(status=status.HTTP_200_OK, data={"message": "Device state change scheduled"})

    def update(self, request, *args, **kwargs):
        return self.request_device_state_change(request)

    def partial_update(self, request, *args, **kwargs):
        return self.request_device_state_change(request)


@api_view(['GET'])
def get_device_parameter_schedule(request, **kwargs):
    """
    Returns schedules for a specific device parameter.
    Check https://ep.iodicus.net/admin/ep/scheduledeviceparametergroup/ for DeviceParameter that are part of a schedule.

    Parameters:

    - pk (int): id of the device parameter to get the schedule for

    Returns:

    - Schedule in crontab format

    Example:

        {
          schedules: [
            {
              crontab: "*/2 * * * * (m/h/d/dM/MY)",
              target_value: 255
            },
            {
              crontab: "1-59/2 * * * * (m/h/d/dM/MY)",
              target_value: 0
            }
          ]
        }


    """

    if 'pk' in kwargs:
        device_param = get_object_or_404(DeviceParameter, pk=kwargs['pk'])
        schedules = device_param.schedule.all()
        if not schedules.exists():
            return Response({"message": "DeviceParameter not in a schedule"}, status=status.HTTP_404_NOT_FOUND)
        res = []
        for schedule in schedules:
            tasks = PeriodicTask.objects.filter(task__exact='ep.tasks.scheduled_device_state_change',
                                                kwargs__contains='"device_group_id":%s' % schedule.id)
            for task in tasks:
                res.append({"crontab": str(task.crontab), "target_value": json.loads(task.kwargs)['target_value']})

            return Response({"schedules": res}, status=status.HTTP_200_OK)
    return Response({"message": "device parameter id not given"}, status=status.HTTP_404_NOT_FOUND)
