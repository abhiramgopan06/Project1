from django.apps import AppConfig

class StoreextrasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'storeextras'

    def ready(self):
        from . import signals
