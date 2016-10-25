import logging

from celery import shared_task

from ep.tasks import ErrorLoggingTask
from prefect.controllers.util import get_controller_for_site_name

logger = logging.getLogger(__name__)


@shared_task(base=ErrorLoggingTask)
def import_from_site(location: str, node_id: int = None):
    logger.info("Importing measurements from %s" % location, extra={'site': location})
    c = get_controller_for_site_name(location)

    c.update(node_id)
