from prefect.controllers.common import BaseController
from prefect.controllers.prefect import PrefectController


def get_controller_for_site_name(site_name) -> BaseController:
    if site_name.lower() == 'badock':
        c = PrefectController.for_badock()
    else:
        c = PrefectController.for_goldney()
    return c
