from django.conf.urls import url
from django.views.decorators.cache import cache_page, never_cache
from rest_framework.urlpatterns import format_suffix_patterns

from ep.apiviews import MeasurementList, SiteList, SiteDetailsView, DeviceParameterDetailsView, NodeList, TariffList, \
    TariffDetailsView, get_device_parameter_schedule, GatewayList, DeviceList, DeviceDetails, \
    MeasurementsLatest

__author__ = 'schien'

urlpatterns = [
    url(r'^schedule/(?P<pk>[0-9]+)$', get_device_parameter_schedule, name='get_device_parameter_schedule'),
    url(r'^device_parameter/(?P<device_parameter_id>[0-9]+)/measurements$', never_cache(MeasurementList.as_view()),
        name='device_measurements'),
    url(r'^device_parameter/(?P<pk>[0-9]+)/measurements/latest$', cache_page(0)(MeasurementsLatest.as_view()),
        name='device_measurements_latest'),
    url(r'^device_parameter/(?P<pk>[0-9]+)$', DeviceParameterDetailsView.as_view(), name='dp_details'),

    url(r'^site$', SiteList.as_view(), name='site_list'),
    url(r'^site/(?P<pk>[0-9]+)$', SiteDetailsView.as_view(), name='site_details'),
    url(r'^site/(?P<pk>[0-9]+)/gateways$', GatewayList.as_view(), name='gateway_for_site'),
    url(r'^site/(?P<pk>[0-9]+)/nodes$', NodeList.as_view(), name='site_nodes'),
    url(r'^site/(?P<pk>[0-9]+)/devices$', DeviceList.as_view(), name='site_devices'),

    url(r'^device/(?P<pk>[0-9]+)$', DeviceDetails.as_view(), name='device_details'),
    url(r'^tariff$', TariffList.as_view(), name='tariff_list'),
    url(r'^tariff/(?P<pk>[0-9]+)$', TariffDetailsView.as_view(), name='tariff_details'),

]

urlpatterns = format_suffix_patterns(urlpatterns)
