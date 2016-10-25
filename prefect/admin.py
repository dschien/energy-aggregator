from django.contrib import admin
from django.core.urlresolvers import reverse

from .models import PrefectDeviceParameterConfiguration

__author__ = 'mitchell'


class PrefectDeviceParameterConfigurationAdmin(admin.ModelAdmin):
    search_fields = ['=device__external_id', '=id', '=line', '=power_consumption']

    # Add it to the list view:
    list_display = ('name',)
    list_filter = ('device__node__gateway', 'device__node__gateway__site')

    # Add it to the details view:
    readonly_fields = ('line', 'power_consumption', 'device_link',)

    def name(self, obj):
        return '{} {}'.format(obj.device, obj.line)

    def device_link(self, obj):
        url = reverse('admin:ep_device_change', args=(obj.device.id,))
        return '<a href="{}">{}</a>'.format(url, obj.device)

    device_link.allow_tags = True
    device_link.short_description = 'Device'

admin.site.register(PrefectDeviceParameterConfiguration, PrefectDeviceParameterConfigurationAdmin)
