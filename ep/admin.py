from django.contrib import admin

# Register your models here.
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.forms import CheckboxSelectMultiple
from weekday_field.fields import WeekdayField

from ep.models import Node, Device, DeviceParameter, Site, Band, Tariff, Gateway, \
    TariffBandProperty, ScheduleDeviceParameterGroup, DPMeasurements, GatewayProperty, NodeProperty


#
# @admin.register()
# class DPMeasurementsModelAdmin(admin.ModelAdmin):
#     def get_urls(self):
#         urls = super(DPMeasurementsModelAdmin, self).get_urls()
#         my_urls = [
#             url(r'^measurements/$', self.admin_site.admin_view(self.my_view))
#         ]
#         return my_urls + urls


class ScheduleDeviceParameterGroupInline(admin.TabularInline):
    model = ScheduleDeviceParameterGroup.device_parameters.through


class DeviceParameterInline(admin.TabularInline):
    model = DeviceParameter
    extra = 0
    show_change_link = True
    readonly_fields = ('type', 'unit', 'last_update_time')

    # def measurements_link(self, obj):
    #     url = reverse('admin:ep_devicestatemeasurement_changelist')
    #     return '<a href="%s?device_parameter=%s">See Measurements</a>' % (url, obj.pk)

    # measurements_link.allow_tags = True
    # measurements_link.short_description = 'Measurements'


class DeviceAdmin(admin.ModelAdmin):
    inlines = [
        DeviceParameterInline,
    ]
    search_fields = ['=external_id', '=node__external_id', '=id']
    # Add it to the list view:
    list_display = ('__str__',)
    list_filter = ('node__gateway', 'node__gateway__site')
    # Add it to the details view:
    readonly_fields = ('node', 'type', 'external_id')


class DeviceParameterAdmin(admin.ModelAdmin):
    # form = CustomDeviceParameterAdminForm

    inlines = [
        ScheduleDeviceParameterGroupInline,
    ]
    search_fields = ['=device__external_id', '=id']

    # Add it to the list view:
    list_display = ('__str__',)
    list_filter = ('device__node__gateway', 'device__node__gateway__site')
    # Add it to the details view:
    readonly_fields = ('type', 'unit', 'device_link', 'latest')

    def latest(self, obj):
        latest = DPMeasurements(obj).latest()
        if latest:
            return "{value} ({time} UTC) ".format(value=latest['value'], time=latest['time'])
        return "-"

    # def measurements_link(self, obj):
    #     url = reverse('admin:ep_devicestatemeasurement_changelist')
    #     return '<a href="%s?device_parameter=%s">See Measurements</a>' % (url, obj.pk)
    #
    # measurements_link.allow_tags = True
    # measurements_link.short_description = 'Measurements'

    def device_link(self, obj):
        url = reverse('admin:ep_device_change', args=(obj.device.id,))
        return '<a href="{}">{}</a>'.format(url, obj.device)

    device_link.allow_tags = True
    device_link.short_description = 'Device'


class DeviceInline(admin.TabularInline):
    model = Device
    extra = 0
    show_change_link = True
    readonly_fields = ('type', 'external_id', 'last_update_time')


class ExternalAdminModelAdmin(admin.ModelAdmin):
    external_admin_group = 'external_admin'
    hidden_fields = []

    def get_form(self, request, obj=None, **kwargs):
        self.fields = [field.name for field in Node._meta.local_concrete_fields if not field.name == 'id']

        if Group.objects.get(name=self.external_admin_group).user_set.filter(id=request.user.id).exists():
            for field_name in self.hidden_fields:
                self.fields.remove(field_name)

        return super(ExternalAdminModelAdmin, self).get_form(request, obj, **kwargs)


class NodePropertyInline(admin.TabularInline):
    model = NodeProperty
    extra = 0
    show_change_link = True


class NodeAdmin(ExternalAdminModelAdmin):
    inlines = [
        NodePropertyInline,
        DeviceInline,
    ]
    search_fields = ['=external_id', '=gateway__site__name', '=id']
    # exclude = ('_most_recent_status',)
    list_filter = ('gateway', 'space_name')
    hidden_fields = ['external_id']
    readonly_fields = ('gateway',)


class DeviceMeasurementAdmin(admin.ModelAdmin):
    date_hierarchy = 'measurement_time'
    search_fields = ['=device_parameter__device__external_id']
    readonly_fields = ('device_parameter_link', 'measurement_time', 'value')
    exclude = ('device_parameter',)
    list_filter = (
        'device_parameter__device__node__gateway__site',
        # 'device_parameter',
        # 'device_parameter__device'
    )

    def device_parameter_link(self, obj):
        url = reverse('admin:ep_deviceparameter_change', args=(obj.device_parameter.id,))
        return '<a href="{}">{}</a>'.format(url, obj.device_parameter)

    device_parameter_link.allow_tags = True
    device_parameter_link.short_description = 'DeviceParameter'


class NodeInline(admin.TabularInline):
    model = Node
    extra = 0
    show_change_link = True

    external_admin_group = 'external_admin'
    hidden_fields = ['external_id']

    def get_formset(self, request, obj=None, **kwargs):
        self.fields = [field.name for field in Node._meta.local_concrete_fields if not field.name == 'id']

        if Group.objects.get(name=self.external_admin_group).user_set.filter(id=request.user.id).exists():
            for field_name in self.hidden_fields:
                self.fields.remove(field_name)

        return super(NodeInline, self).get_formset(request, obj, **kwargs)


class GatewayPropertyInline(admin.TabularInline):
    model = GatewayProperty
    extra = 0
    show_change_link = True


@admin.register(Gateway)
class GatewayAdmin(admin.ModelAdmin):
    inlines = [
        NodeInline, GatewayPropertyInline
    ]


class GatewayInline(admin.TabularInline):
    model = Gateway
    extra = 0
    show_change_link = True


class BandInline(admin.TabularInline):
    model = Band
    extra = 0
    show_change_link = True


class TariffBandPropertyInline(admin.TabularInline):
    model = TariffBandProperty
    extra = 0
    show_change_link = True


@admin.register(Band)
class BandAdmin(admin.ModelAdmin):
    inlines = [
        TariffBandPropertyInline,
    ]

    formfield_overrides = {
        WeekdayField: {'widget': CheckboxSelectMultiple},
    }


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    inlines = [
        BandInline,
    ]


@admin.register(ScheduleDeviceParameterGroup)
class ScheduleDeviceParameterGroupAdmin(admin.ModelAdmin):
    # inlines = [
    #     ScheduleDeviceParameterGroupInline,
    # ]
    # exclude = ('device_parameters',)
    # raw_id_fields = ("device_parameters",)
    pass


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    inlines = [GatewayInline]


admin.site.register(Node, NodeAdmin)
admin.site.register(Device, DeviceAdmin)
admin.site.register(DeviceParameter, DeviceParameterAdmin)
# admin.site.register(DeviceStateMeasurement, DeviceMeasurementAdmin)
