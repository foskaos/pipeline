from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.db.models import Func, OuterRef, Subquery, Value, QuerySet
from django.db.models.functions import Coalesce
from .core import Schedule


class IncrementalLog(models.Model):
    # We force the ID to always be 1 so there can be only one row.
    id = models.IntegerField(primary_key=True, default=1)
    schedule_id = models.IntegerField(default=0)
    journey_id = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        self.id = 1  # Ensure the primary key is always 1
        super().save(*args, **kwargs)


class BaseStagingManager(models.Manager):
    """
    Base Class for incremental loading into a staging table
    """
    def __init__(self, table_key, table_model, incremental_key):
        super().__init__()
        self.table_key = table_key
        self.table_model = table_model
        self.incremental_key = incremental_key

    def get_last_loaded(self):
        """Retrieve the last loaded schedule ID from the incremental log."""
        last_loaded = IncrementalLog.objects.order_by(f'-{self.table_key}').first()
        if last_loaded:
            return last_loaded
        return IncrementalLog.objects.create()

    def populate_from_unmanaged(self, mock_increment = 0):
        """Populates Schedule objects from unmanaged database incrementally.
           Also tracks the last loaded ID to enable incremental loading of this table
        """

        last_loaded = self.get_last_loaded()

        last_loaded_id = getattr(last_loaded, self.table_key)

        # Fetch new records from unmanaged source
        if mock_increment:
            instances = self.table_model.objects.filter(**{f"{self.incremental_key}__lt": mock_increment})
        else:
            instances = self.table_model.objects.filter(
                **{f"{self.incremental_key}__gt": last_loaded_id}
            ).order_by(self.incremental_key)

        if instances.exists():
            self.bulk_create(instances, ignore_conflicts=True)  # Bulk insert, avoiding duplicates
            # Store max ID loaded in IncrementalLog
            max_id = instances.aggregate(models.Max(self.incremental_key))[f'{self.incremental_key}__max']
            setattr(last_loaded, self.table_key, max_id)
            last_loaded.save()


class StagingScheduleModel(models.Model):
    id = models.IntegerField(primary_key=True)
    slug = models.CharField(max_length=255)
    # extracted_numbers = ArrayField(models.CharField(max_length=200,default=None), blank=True, default=list)
    StagingScheduleManager = BaseStagingManager(table_key='schedule_id',
                                                table_model=Schedule,
                                                incremental_key='id')
    objects = StagingScheduleManager

    @classmethod
    def with_extracted_numbers(cls) -> models.QuerySet:
        """
        Annotates each Schedule instance with an array of numbers extracted from `slug`
        using PostgreSQL's `regexp_matches()`, ensuring rows with no matches are included.
        """

        class RegexpMatches(Func):
            function = 'REGEXP_MATCHES'
            arity = 2  # Requires two arguments (column, regex pattern)

        extracted_numbers_subquery = (
            cls.objects.filter(id=OuterRef("id"))
            .annotate(matches=RegexpMatches("slug", Value(r"(\d+[dwmy])(?:-(\d+[dwmy]))*(?:-(.*))")))
            .values("matches")  # Extract only the matches column
        )

        return cls.objects.annotate(
            extracted_numbers=Coalesce(
                Subquery(extracted_numbers_subquery,
                         output_field=ArrayField(models.CharField(max_length=255), default=list)),
                Value([])
            ))

    class Meta:
        db_table = 'staging_schedule'