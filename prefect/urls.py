

from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

from ep.views import NodeListView, DeviceParameterDetailView
from prefect.views import DeviceDetailView

__author__ = 'schien'

urlpatterns = [
    url(r'^(?P<site>[\w]+)/(?P<prefect_id>[0-9]+)$',
        login_required(DeviceDetailView.as_view()),
        name='device-detail'),
    url(r'^devices$', login_required(NodeListView.as_view()), name='prefectdevice-list'),
    url(r'^(?P<site>[\w]+)$', login_required(NodeListView.as_view()),
        name='prefectdevice-list'),
    url(r'^device/(?P<device_parameter_id>[0-9]+)$',
        login_required(DeviceParameterDetailView.as_view()),
        name='device-parameter-detail'),
]
