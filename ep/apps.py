from django.apps import AppConfig


class EnergyPortalConfig(AppConfig):
    name = 'ep'
    verbose_name = "IODiCUS Energy Portal"

    def ready(self):
        # noinspection UnusedImport
        import ep.signals.handlers  # noqa
