# Create your views here.
import logging

from django.views.generic import TemplateView
from django.views.generic.list import ListView

from ep.models import Node, DeviceParameter, Gateway

logger = logging.getLogger(__name__)


class NodeListView(ListView):
    queryset = Node.objects.all()

    def get_queryset(self):
        if 'site' in self.kwargs:
            gateways = Gateway.objects.filter(site=self.kwargs['site'])
            return Node.objects.filter(gateway__site_id__in=gateways)

        else:
            return super().get_queryset()

    def get_context_data(self, **kwargs):
        context = super(NodeListView, self).get_context_data(**kwargs)
        return context


class DeviceDetailView(TemplateView):
    template_name = 'ep/device_detail.html'

    def get_context_data(self, **kwargs):
        context = super(DeviceDetailView, self).get_context_data(**kwargs)
        node_id = kwargs['pk']
        dev = Node.objects.get(node_id)
        context['node'] = dev
        return context


class DeviceParameterDetailView(TemplateView):
    template_name = 'ep/device_param_detail.html'

    def get_context_data(self, **kwargs):
        context = super(DeviceParameterDetailView, self).get_context_data(**kwargs)
        param_id = self.kwargs['device_parameter_id']
        device_param = DeviceParameter.objects.get(id=param_id)

        context['device_param'] = device_param
        return context


class SimpleVisView(TemplateView):
    # chose template
    template_name = 'ep_vis/IndivNode.html'

    def get_context_data(self, **kwargs):
    #     # define json var data, metadata, etc
    #     context = super(DeviceParameterDetailView, self).get_context_data(**kwargs)
    #     param_id = self.kwargs['device_parameter_id']
    #     device_param = DeviceParameter.objects.get(id=param_id)
    #
    #     data_var = ['data':'
    # {
    #     "Temperature": 18.8,
    #     "Presence": 0,
    #     "ProgramName": "Unoccupied",
    #     "DateTimeRecieved": "2016-06-23 00:09:43",
    #     "TempAdjusted": 0,
    #     "L2Relay": 0,
    #     "EnergyWh": 0.0,
    #     "TempSetPoint": 14.0
    # }']
    #
    #     context['data'] = data_var
    #     context['metadata'] = device_param

        return super().get_context_data()