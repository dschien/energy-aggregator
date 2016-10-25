from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

from ep.views import NodeListView, DeviceParameterDetailView, DeviceDetailView

__author__ = 'schien'

urlpatterns = [
    url(r'^$',
        TemplateView.as_view(template_name="ep/index.html"),
        name="home"),
    url(r'^devices$', login_required(NodeListView.as_view()), name='device-list'),
    url(r'^(?P<site>[\w]+)$', login_required(NodeListView.as_view()),
        name='device-list'),
    url(r'^(?P<pk>[0-9]+)$',
        login_required(DeviceDetailView.as_view()),
        name='device-detail'),
    url(r'^device/(?P<device_parameter_id>[0-9]+)$',
        login_required(DeviceParameterDetailView.as_view()),
        name='device-parameter-detail'),
    url(r'no_login', TemplateView.as_view(template_name="ep/nologin.html")),
    url(r'^vis',
        TemplateView.as_view(template_name="ep_vis/IndivNode.html"),
        name="vis-indv-node")
]
