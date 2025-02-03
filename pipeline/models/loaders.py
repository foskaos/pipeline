from django.db import models, transaction

from django.db.models import Field

class FullLoadManager(models.Manager):

    def __init__(self, table_model):
        super().__init__()
        self.table_model = table_model

    def populate_from_unmanaged(self):
        """Populates  objects from unmanaged database with full refresh
        """

        staging_fields = {
            f.name for f in self.model._meta.get_fields()
            if isinstance(f, Field) and not f.auto_created
        }

        # Get all non-auto-created fields from the old model:
        source_fields = [
            f.name for f in self.table_model._meta.get_fields()
            if isinstance(f, Field) and not f.auto_created
        ]

        # Fetch all records from unmanaged source as a generator, 100K items at a time
        instances = self.table_model.objects.all().values(*source_fields).iterator()

        if first_instance := next(instances, None):
            # if we have something in the generator time to full load so clear out the destination table
            self.model.objects.all().delete()
        else:
            return

        batch = [self.model(**first_instance)]
        batch_size = 100_000
        batch_counter = 1
        # load in batches
        for obj in instances:
            batch.append(self.model(**obj))
            if len(batch) >= batch_size:
                print(f"Inserting batch {batch_counter}: {len(batch)} records.")
                with transaction.atomic():
                    self.model.objects.bulk_create(batch, ignore_conflicts=False)
                batch_counter += 1
                batch = []

        if batch:
            print(f"Inserting last batch: {len(batch)} records.")
            with transaction.atomic():
                self.model.objects.bulk_create(batch, ignore_conflicts=False)


class IncrementalManager(models.Manager):
    """
    Base Class for incremental loading into a staging table
    """
    def __init__(self, table_key, table_model, incremental_key, incremental_model):
        super().__init__()
        self.table_key = table_key
        self.table_model = table_model
        self.incremental_key = incremental_key
        self.incremental_model = incremental_model

    def get_last_loaded(self):
        """Retrieve the last loaded schedule ID from the incremental log."""
        last_loaded = self.incremental_model.objects.order_by(f'-{self.table_key}').first()
        if last_loaded:
            return last_loaded
        return self.incremental_model.objects.create()

    def populate_from_unmanaged(self, mock_increment = 0):
        """Populates table from unmanaged database incrementally.
           Also tracks the last loaded ID to enable incremental loading of this table
        """

        last_loaded = self.get_last_loaded()
        last_loaded_id = getattr(last_loaded, self.table_key)

        # Get all non-auto-created fields from the old model:
        source_fields = [
            f.name for f in self.table_model._meta.get_fields()
            if isinstance(f, Field) and not f.auto_created
        ]

        if mock_increment:
            print(f'Loading values less than {mock_increment}')
            instances = self.table_model.objects.filter(**{f"{self.incremental_key}__lt": mock_increment}).values(
                *source_fields).iterator()
        else:
            if not last_loaded_id:
                print(f'Loading all values as there was nothing in the incremental log')
                self.model.objects.all().delete()  # redundant, but if we are here, its a good safety net
                instances = self.table_model.objects.all().order_by(self.incremental_key).values(
                    *source_fields).iterator()
            else:
                print(f'Loading values greater than {last_loaded_id}')
                instances = self.table_model.objects.filter(
                    **{f"{self.incremental_key}__gt": last_loaded_id}
                ).order_by(self.incremental_key).values(*source_fields).iterator()

        if first_instance := next(instances, None):
            # if we have something in the generator time to full load so clear out the destination table
            self.model.objects.all().delete()
        else:
            return

        batch = [self.model(**first_instance)]
        batch_size = 100_000
        batch_counter = 1
        # load in batches
        for obj in instances:
            batch.append(self.model(**obj))
            if len(batch) >= batch_size:
                print(f"Inserting batch {batch_counter}: {len(batch)} records.")
                with transaction.atomic():
                    self.model.objects.bulk_create(batch, ignore_conflicts=True)
                batch_counter += 1
                batch = []

        if batch:
            print(f"Inserting last batch: {len(batch)} records.")
            with transaction.atomic():
                self.model.objects.bulk_create(batch, ignore_conflicts=True)

        # find the max value for the incremental key and load that in to the incremental log
        max_id = self.model.objects.aggregate(models.Max(self.incremental_key))[f'{self.incremental_key}__max']
        setattr(last_loaded, self.table_key, max_id)
        last_loaded.save()


