from django.db import models, transaction
from django.db.models.fields.related import ManyToManyField

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
            if isinstance(f, Field) and (not f.auto_created and not f.is_relation)
        ]

        destination_fields = [
            f.name for f in self.model._meta.get_fields()
            if isinstance(f, Field) and (not f.auto_created and not f.is_relation)
        ]

        # Fetch all records from unmanaged source as a generator, 100K items at a time
        instances = self.table_model.objects.all().values(*source_fields).iterator()

        if first_instance := next(instances, None):
            # if we have something in the generator time to full load so clear out the destination table
            self.model.objects.all().delete()
        else:
            return

        related_fields_for_model = [fld for fld in self.model._meta.get_fields() if fld.is_relation and not fld.auto_created]

        out = {}
        for r in related_fields_for_model:
            # if isinstance(r, ManyToManyField):
            if r.many_to_many:
                continue
            related_column_name = r.related_fields[0][1].name
            related_objs = list(r.related_model.objects.all())
            dicky = {getattr(obj, related_column_name): obj for obj in related_objs}
            out[r.related_model.__name__] = dicky

        loading_log = []
        def build_dest_model(instance):

            for fld in related_fields_for_model:

                if isinstance(fld, ManyToManyField):
                    continue
                related_column_name = fld.related_fields[0][1].name
                related_model_name = fld.related_model.__name__
                try:
                    related_obj = out[related_model_name][instance[fld.name]]
                    # related_field = fld.related_model.objects.get(**{related_column_name:instance[fld.name]})
                except KeyError as e:
                    # print(f"Found Missing value for {fld.name}: {e}")
                    error_log = ('Missing Value',fld.name,instance)
                    loading_log.append(error_log)
                    # here the schedule doesn't exist in the schedule table
                    related_obj = None

                instance[fld.name] = related_obj

            return self.model(**instance)

        batch = [build_dest_model(first_instance)]
        # import ipdb; ipdb.set_trace()
        batch_size = 100_000
        batch_counter = 1
        # load in batches
        for obj in instances:
            batch.append(build_dest_model(obj))
            if len(batch) >= batch_size:
                print(f"Inserting batch {batch_counter}: {len(batch)} records.")
                with transaction.atomic():
                    self.model.objects.bulk_create(batch, ignore_conflicts=False)
                batch_counter += 1
                batch = []
        # import ipdb; ipdb.set_trace()
        if batch:
            print(f"Inserting last batch: {len(batch)} records.")
            with transaction.atomic():
                self.model.objects.bulk_create(batch, ignore_conflicts=False)

        return loading_log


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
        loading_log = []

        last_loaded = self.get_last_loaded()
        last_loaded_id = getattr(last_loaded, self.table_key)

        # Get all non-auto-created fields from the old model:
        source_fields = [
            f.name for f in self.table_model._meta.get_fields()
            if isinstance(f, Field) and (not f.auto_created and not f.is_relation)
        ]

        # related_destination_fields = [
        #     f.name for f in self.model._meta.get_fields()
        #     if isinstance(f, Field) and (not f.auto_created and f.is_relation)
        # ]

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
            return loading_log

        related_fields_for_model = [fld for fld in self.model._meta.get_fields() if fld.is_relation and not fld.auto_created]


        out = {}
        for r in related_fields_for_model:
            if isinstance(r, ManyToManyField):
                continue
            related_column_name = r.related_fields[0][1].name
            related_objs = list(r.related_model.objects.all())
            dicky = {getattr(obj, related_column_name): obj for obj in related_objs}
            out[r.related_model.__name__] = dicky
        def build_dest_model(instance):


            for fld in related_fields_for_model:

                if isinstance(fld, ManyToManyField):
                    continue
                related_column_name = fld.related_fields[0][1].name
                related_model_name = fld.related_model.__name__
                try:
                    related_obj = out[related_model_name][instance[fld.name]]
                    # related_field = fld.related_model.objects.get(**{related_column_name:instance[fld.name]})
                except KeyError as e:
                    error_log = ('Missing Value', fld.name, instance)
                    loading_log.append(error_log)
                    #print(f"Found Missing value for {fld.name}: {e}")
                    # here the schedule doesn't exist in the schedule table
                    related_obj = None

                instance[fld.name] = related_obj

            return self.model(**instance)

        batch = [build_dest_model(first_instance)]
        batch_size = 100_000
        batch_counter = 1
        # load in batches
        for obj in instances:
            batch.append(build_dest_model(obj))
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

        return loading_log


