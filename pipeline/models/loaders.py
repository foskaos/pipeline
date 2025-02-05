from django.db import models, transaction
from typing import Iterable
from django.db.models import Field, F
from abc import ABC, abstractmethod

import logging
import time
import re

logger = logging.getLogger('Pipeline Runner')
logging.basicConfig(level=logging.INFO, format='[%(levelname)s]: %(message)s')


class ColumnTransformer(ABC):

    @property
    @abstractmethod
    def input_field(self) -> str:
        """The name of the input field."""

        pass

    @property
    @abstractmethod
    def output_fields(self) -> list:
        """A tuple of output field names."""

        pass

    @classmethod
    @abstractmethod
    def transform(cls, value):
        """
        Transform the input value to the output field(s).
        """
        pass


class ScheduleWindowTransformer(ColumnTransformer):
    SLUG_REGEX = re.compile(
        r"(\d+[dwmy])(?:-(\d+[dwmy]))*(?:-(.*))"
    )

    @property
    def input_field(self) -> str:
        return 'slug'

    @property
    def output_fields(self) -> list:
        return ['id', 'schedule', 'schedule_offset_start', 'schedule_offset_end', 'schedule_milestone_slug']

    @staticmethod
    def convert_to_days(s: str) -> int | None:
        num = int(str(s[:-1]))
        char = s[-1]
        match char:
            case 'd':
                return num * 1
            case 'w':
                return num * 7
            case 'm':
                return num * 30
            case 'y':
                return num * 365
            case _:
                return None  # Handle invalid input

    @staticmethod
    def extract_milestone(slug_part: str) -> str | None:
        milestones = {
            "op": "operation",
            "appt": "appointment",
            "reg": "registration",
            "po": "operation",
            "dis": "discharge",
        }

        for key, value in milestones.items():
            if key in slug_part:
                return value
        # if we don't know what milestone put unknown
        return 'unknown'

    @staticmethod
    def extract_offset_sign(slug_part: str) -> int | None:
        if 'pre' in slug_part:
            return -1
        return 1

    @classmethod
    def process_slug(cls, slug: str) -> dict:

        if res := re.search(cls.SLUG_REGEX, slug):
            # extract by position
            start, end, identifier = res.groups()
            offset_sign = cls.extract_offset_sign(identifier)
            ms = cls.extract_milestone(identifier)

            offset_start = cls.convert_to_days(start) * offset_sign
            offset_end = cls.convert_to_days(end) * offset_sign if res.group(2) else None
            milestone_slug = ms

            # validation: schedule end is greater that start
            if offset_end:
                if offset_end < offset_start:
                    logger.warning(f"Slug offsets are invalid: {offset_start}, {offset_end}, {slug}")
                    return {}

            return {
                'schedule_offset_start': offset_start,
                'schedule_offset_end': offset_end,
                'schedule_milestone_slug': milestone_slug,
            }

        return {}

    @classmethod
    def transform(cls, slug: str) -> dict:

        return cls.process_slug(slug)


class DataLoader(models.Manager):
    def __init__(self):
        super().__init__()
        self.log = []

    @staticmethod
    def make_related_fields_lookup(related_fields_for_model) -> dict:
        """
        # Make a dictionary with related fields for fast lookup in batch loading
        # This makes a massive memory vs performance trade off
        """
        related_lookup = {}
        for field in related_fields_for_model:
            if field.many_to_many:
                continue
            related_column_name = field.related_fields[0][1].name
            related_objs = list(field.related_model.objects.all())
            model_id_to_native_instance = {getattr(obj, related_column_name): obj for obj in related_objs}
            related_lookup[field.related_model.__name__] = model_id_to_native_instance

        return related_lookup

    def build_output_object(self,
                            instance: dict,
                            related_fields_for_model: list[models.Field],
                            related_field_lookup: dict) -> models.Model:

        for fld in related_fields_for_model:
            if fld.many_to_many:
                continue
            related_model_name = fld.related_model.__name__
            try:
                related_obj = related_field_lookup[related_model_name][instance[fld.name]]
            except KeyError as e:
                # Looks like we have an integrity problem, set to null
                error_log = ('Missing Value', fld.name, instance)
                self.log.append(error_log)
                related_obj = None
            instance[fld.name] = related_obj
        return self.model(**instance)

    def batch_loader(self,
                     batch_size: int,
                     first: dict,
                     instances_to_load: Iterable,
                     related_field_lookup: dict,
                     related_fields_for_model: list) -> None:
        batch = [self.build_output_object(first, related_fields_for_model, related_field_lookup)]

        batch_counter = 1
        record_counter = 1

        # load in batches using atomic transactions for safety
        for obj in instances_to_load:
            output_model = self.build_output_object(obj, related_fields_for_model, related_field_lookup)
            if not output_model:
                continue
            batch.append(output_model)
            record_counter += 1
            if len(batch) >= batch_size:
                logger.info(f"Inserting batch {batch_counter}: {len(batch)} records.")
                with transaction.atomic():
                    self.model.objects.bulk_create(batch, ignore_conflicts=False)
                batch_counter += 1
                batch = []

        if batch:
            logger.info(f"Inserting last batch: {len(batch)} records.")
            with transaction.atomic():
                self.model.objects.bulk_create(batch, ignore_conflicts=False)
        logger.info(f"{self.model.__name__} Loaded {record_counter} records.")
        self.log.append(("Loaded Values", self.model.__name__, record_counter))

    def execute_pipeline(self, first_instance, instances_to_load: Iterable) -> None:

        logger.info(f"Executing {self.LOAD_TYPE} for {self.model.__name__}")
        start = time.time()
        related_fields_for_model = [fld for fld in self.model._meta.get_fields() if
                                    fld.is_relation and not fld.auto_created]

        related_field_lookup = self.make_related_fields_lookup(related_fields_for_model)

        self.batch_loader(
            100_000,
            first_instance,
            instances_to_load,
            related_field_lookup,
            related_fields_for_model
        )

        duration = (time.time() - start)
        logger.info(f"{self.model.__name__} took: {duration:.2f} seconds")


class FullLoadManager(DataLoader):
    LOAD_TYPE = "Full Load"

    def __init__(self, table_model):
        super().__init__()
        self.table_model = table_model

    def full_load_query(self):
        """
        Query for full table load
        """
        source_fields = [
            f.name for f in self.table_model._meta.get_fields()
            if isinstance(f, Field) and (not f.auto_created and not f.is_relation)
        ]
        # Fetch all records from unmanaged source as a generator, 100K items at a time
        instances = self.table_model.objects.all().values(*source_fields).iterator()
        return instances

    def populate_model(self):
        """Populates objects from unmanaged database with full refresh
        """
        instances = self.full_load_query()

        # check if we have any instances.
        if first_instance := next(instances, None):
            # if we have something in the generator time to full load so clear out the destination table
            self.model.objects.all().delete()
        else:
            return None

        # run the batch loading pipeline
        self.execute_pipeline(first_instance, instances)

        return self.log


class IncrementalLoadManager(DataLoader):
    LOAD_TYPE = "Incremental Load"

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

    def incremental_load_query(self, last_loaded_id, mock_increment=0):

        # Get all non-auto-created fields from the old model:
        source_fields = [
            f.name for f in self.table_model._meta.get_fields()
            if isinstance(f, Field) and (not f.auto_created and not f.is_relation)
        ]
        if mock_increment:
            logger.info(f'Loading values less than {mock_increment}')
            instances = self.table_model.objects.filter(**{f"{self.incremental_key}__lt": mock_increment}).values(
                *source_fields).iterator()
        else:
            if not last_loaded_id:
                logger.info(f'Loading all values as there was nothing in the incremental log')
                self.model.objects.all().delete()  # redundant, but if we are here, its a good safety net
                instances = self.table_model.objects.all().order_by(self.incremental_key).values(
                    *source_fields).iterator()
            else:
                # logger.info(f'Loading values greater than {last_loaded_id}')
                instances = self.table_model.objects.filter(
                    **{f"{self.incremental_key}__gt": last_loaded_id}
                ).order_by(self.incremental_key).values(*source_fields).iterator()

        return instances

    def populate_model(self, mock_increment=0):
        """Populates table from unmanaged database incrementally.
           Also tracks the last loaded ID to enable incremental loading of this table
        """

        last_loaded = self.get_last_loaded()
        last_loaded_id = getattr(last_loaded, self.table_key)

        instances = self.incremental_load_query(last_loaded_id, mock_increment)

        if first_instance := next(instances, None):
            # if we have something in the generator time to full load so clear out the destination table
            logger.info(f'Loading values greater than {last_loaded_id}')
        else:
            logger.info(f'Nothing new to load for {self.model.__name__}')
            return self.log
        # run the batch loading pipeline
        self.execute_pipeline(first_instance, instances)

        # find the max value for the incremental key and load that in to the incremental log
        max_id = self.model.objects.aggregate(models.Max(self.incremental_key))[f'{self.incremental_key}__max']
        setattr(last_loaded, self.table_key, max_id)
        last_loaded.save()

        return self.log


class IncrementalTransformLoadManager(IncrementalLoadManager):

    def __init__(self, table_key, table_model, incremental_key, incremental_model, transformer: ColumnTransformer):
        super().__init__(table_key, table_model, incremental_key, incremental_model)
        self.table_key = table_key
        self.table_model = table_model
        self.incremental_key = incremental_key
        self.incremental_model = incremental_model
        self.transformer = transformer

    def build_output_object(self,
                            instance: dict,
                            related_fields_for_model: list[models.Field],
                            related_field_lookup: dict) -> models.Model:

        for fld in related_fields_for_model:
            if fld.many_to_many:
                continue
            related_model_name = fld.related_model.__name__
            relation_name = fld.related_fields[0][1].name
            try:
                related_obj = related_field_lookup[related_model_name][instance[relation_name]]
            except KeyError as e:
                # Looks like we have an integrity problem, set to null
                error_log = ('Missing Value', fld.name, instance)
                self.log.append(error_log)
                related_obj = None
            instance[fld.name] = related_obj

        # add extra stuff here

        if self.transformer:

            input_col = self.transformer.input_field
            columns_to_add = self.transformer.transform(instance[input_col])

            if columns_to_add:
                combined_dictionary = instance | columns_to_add

                output = {col_name: value
                          for col_name, value in combined_dictionary.items()
                          if col_name in self.transformer.output_fields}

                return self.model(**output)
            else:
                return None

        return self.model(**instance)


class FullLoadQueryManager(FullLoadManager):

    def __init__(self, table_model, query=None):
        super().__init__(table_model)

        self.query = query

    def full_load_query(self):
        # Fetch all records from provided query
        return self.query()

    def build_output_object(self, instance, *args, **kwargs):
        """
        slightly modified from other loaders as is more simple here
        """
        output = {}
        for r in self.model._meta.get_fields():
            if r.name == 'id':
                continue
            if r.is_relation:
                # add _id suffix for foreign key relationships
                output[f"{r.name}_id"] = instance[r.name]
            else:
                output[f"{r.name}"] = instance[r.name]

        return self.model(**output)
