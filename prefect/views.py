import logging

from django.shortcuts import render, get_object_or_404

# Create your views here.
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ep.models import Node, Site
from .tasks import import_from_site

logger = logging.getLogger(__name__)


class DeviceDetailView(TemplateView):
    template_name = 'ep/device_detail.html'

    def get_context_data(self, **kwargs):
        context = super(DeviceDetailView, self).get_context_data(**kwargs)
        node_id = kwargs['pk']
        dev = Node.objects.get(node_id)
        context['node'] = dev
        return context


@api_view(['GET'])
def import_from_site_view(request, **kwargs):
    """
    Trigger import of from this LES.

    """

    if 'pk' in kwargs:
        site = get_object_or_404(Site, pk=kwargs['pk'])
        logger.info("Manual trigger of import for Site {}".format(site.name), extra={'site': site.name})
        import_from_site.delay(site.name)

        return Response({"message": "Triggered Import for {}".format(site.name)}, status=status.HTTP_200_OK)
    return Response({"message": "Site not found"}, status=status.HTTP_404_NOT_FOUND)
