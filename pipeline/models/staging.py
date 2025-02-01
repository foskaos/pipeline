from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.db.models import Func, OuterRef, Subquery, Value, QuerySet
from django.db.models.functions import Coalesce
from .core import Schedule


class IncrementalLog(models.Model):
    schedule_id = models.IntegerField()
    journey_id = models.IntegerField()



class ProcessedScheduleManager(models.Manager):

    def populate_from_unmanaged(self):
        """Populates Schedule objects from unmanaged database"""
        instances = Schedule.objects.filter(id__lt=600)
        self.bulk_create(instances, ignore_conflicts=True)  # Bulk insert, avoiding duplicates


class StagingScheduleModel(models.Model):
    id = models.IntegerField(primary_key=True)
    slug = models.CharField(max_length=255)
    # extracted_numbers = ArrayField(models.CharField(max_length=200,default=None), blank=True, default=list)
    objects = ProcessedScheduleManager()

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