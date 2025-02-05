from django.apps import AppConfig


class PipelineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pipeline'

    def ready(self):
        # load models module
        from .models import core, staging, analytics
