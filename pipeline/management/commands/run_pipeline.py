import logging
from django.core.management.base import BaseCommand
from pipeline.models.staging import staging_pipeline
from pipeline.models.analytics import analytics_pipeline
logger = logging.getLogger('Pipeline Runner')

def execute_pipeline(pipeline):
    """
    Execute a pipeline of models with population from unmanaged sources.

    Args:
        pipeline (list): List of model classes to process

    Returns:
        dict: Analytics log with results for each model
    """
    analytics_log = {}
    for model in pipeline:
        try:
            mval_log = model.objects.populate_model()
            analytics_log[model.__name__] = mval_log
        except Exception as e:
            logger.error(f"Error loading {model.__name__}:\n\t\t{e}")
            import traceback
            traceback.print_exc()
            break

    return analytics_log


class Command(BaseCommand):
    help = 'Run data pipeline for staging and analytics models'

    def add_arguments(self, parser):
        """
        Optional arguments for the command.
        You can add flags to control pipeline execution if needed.
        """
        parser.add_argument(
            '--skip-staging',
            action='store_true',
            help='Skip staging pipeline execution'
        )
        parser.add_argument(
            '--skip-analytics',
            action='store_true',
            help='Skip analytics pipeline execution'
        )
        parser.add_argument(
            '--print-logs',
            action='store_true',
            default=False,
            help='Skip analytics pipeline execution'
        )

    def handle(self, *args, **options):
        """
        Main command execution method.

        Modify staging_pipeline and analytics_pipeline
        to include your specific model classes.
        """
        # Import your model classes here to avoid circular imports

        # Execute pipelines based on command options
        if not options['skip_staging']:
            self.stdout.write('Starting staging pipeline...')
            staging_log = execute_pipeline(staging_pipeline)
            self.stdout.write(self.style.SUCCESS('Staging pipeline completed'))

            # Optional: log details about staging pipeline execution
            if options['print_logs']:
                for model_name, log_entry in staging_log.items():
                    self.stdout.write(f'{model_name}: {log_entry}')

        if not options['skip_analytics']:
            self.stdout.write('Starting analytics pipeline...')
            analytics_log = execute_pipeline(analytics_pipeline)
            self.stdout.write(self.style.SUCCESS('Analytics pipeline completed'))

            # Optional: log details about analytics pipeline execution
            if options['print_logs']:
                for model_name, log_entry in analytics_log.items():
                    self.stdout.write(f'{model_name}: {log_entry}')

# Usage example:
# python manage.py run_pipeline
# python manage.py run_pipeline --skip-staging
# python manage.py run_pipeline --skip-analytics