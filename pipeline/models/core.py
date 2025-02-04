# This set of models represents the transactional database, and is unmanaged.
# The point of this is to provide a Django Native interface


from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.db.models import Func, OuterRef, Subquery, Value, QuerySet
from django.db.models.functions import Coalesce




class ExternalDatabaseModel(models.Model):
    class Meta:
        abstract = True
        managed = False
        app_label = 'msk_db'

    def save(self, *args, **kwargs):
        raise NotImplementedError("This model is read-only.")


class Schedule(ExternalDatabaseModel):
    id = models.IntegerField(primary_key=True)
    slug = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'schedule'
    #
    # @classmethod
    # def with_extracted_numbers(cls) -> models.QuerySet:
    #     """
    #     Annotates each Schedule instance with an array of numbers extracted from `slug`
    #     using PostgreSQL's `regexp_matches()`, ensuring rows with no matches are included.
    #     """
    #
    #     class RegexpMatches(Func):
    #         function = 'REGEXP_MATCHES'
    #         arity = 2  # Requires two arguments (column, regex pattern)
    #
    #     extracted_numbers_subquery = (
    #         cls.objects.filter(id=OuterRef("id"))
    #         .annotate(matches=RegexpMatches("slug", Value(r"(\d+[dwmy])(?:-(\d+[dwmy]))*(?:-(.*))")))
    #         .values("matches")  # Extract only the matches column
    #     )
    #
    #     return cls.objects.annotate(
    #         extracted_numbers=Coalesce(
    #             Subquery(extracted_numbers_subquery, output_field=ArrayField(models.CharField(max_length=255), default=list)),
    #             Value([])
    #     ))



class Activity(ExternalDatabaseModel):
    id = models.IntegerField(primary_key=True)
    content_slug = models.CharField(max_length=255)
    schedule_id = models.IntegerField()#ForeignKey(Schedule, on_delete=models.CASCADE, db_column='schedule_id', db_constraint=False)

    class Meta:
        managed = False
        db_table = 'activity'


class Device(ExternalDatabaseModel):
    id = models.IntegerField(primary_key=True)
    platform = models.CharField(max_length=50)
    os_version = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'device'


class Journey(ExternalDatabaseModel):
    id = models.IntegerField(primary_key=True)
    abbreviation = models.CharField(max_length=255)
    joint_slug = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'journey'


class JourneyActivity(ExternalDatabaseModel):
    journey_id = models.IntegerField(primary_key=True, unique=False)
    activity_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'journey_activity'


class Patient(ExternalDatabaseModel):
    id = models.IntegerField(primary_key=True)
    age_bracket = models.CharField(max_length=50)
    sex = models.CharField(max_length=50)
    hospital = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'patient'


class PatientJourney(ExternalDatabaseModel):
    id = models.IntegerField(primary_key=True)
    patient_id = models.IntegerField()
    journey_id = models.IntegerField()
    invitation_date = models.DateField()
    registration_date = models.DateField()
    operation_date = models.DateField()
    discharge_date = models.DateField()
    consent_date = models.DateField()
    clinician_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'patient_journey'


class StepResult(ExternalDatabaseModel):
    patient_id = models.IntegerField(primary_key=True, unique=False)
    date = models.DateField()
    value = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'step_result'


class Survey(ExternalDatabaseModel):
    id = models.IntegerField(primary_key=True)
    slug = models.CharField(max_length=255)
    version = models.CharField(max_length=50)
    tags = ArrayField(models.CharField(max_length=200), blank=True)

    class Meta:
        managed = False
        db_table = 'survey'


class SurveyResult(ExternalDatabaseModel):
    id = models.AutoField(primary_key=True)
    patient_journey_id = models.IntegerField()
    survey_id = models.IntegerField()
    activity_id = models.IntegerField()
    device_id = models.IntegerField()
    score_value = models.IntegerField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'survey_result'
#
# class ProcessedModelQuerySet(models.QuerySet):
#     def from_unmanaged_data(self):
#         # Extract data from the unmanaged model, apply transformations
#         records = Survey.objects.all()
#
#         #            filter(
#         #     created_at__gte="2024-01-01"  # Example condition
#         # ).values("id", "raw_field"))  # Select only necessary fields
#         import ipdb; ipdb.set_trace()
#         bulk_instances = [
#             ProcessedSurveyModel(
#                 id=record.id,
#                 slug=record.slug.upper(),  # Example transformation
#                 version=record.version,
#                 tags=record.tags if record.tags else []
#             )
#             for record in records
#         ]
#         return bulk_instances
#
#
# class ProcessedModelManager(models.Manager):
#     def get_queryset(self):
#         return ProcessedModelQuerySet(self.model, using=self._db)
#
#     def populate_from_unmanaged(self):
#         instances = self.get_queryset().from_unmanaged_data()
#         self.bulk_create(instances, ignore_conflicts=True)  # Bulk insert, avoiding duplicates
#
#
# class ProcessedSurveyModel(models.Model):
#     id = models.IntegerField(primary_key=True)
#     slug = models.CharField(max_length=255)
#     version = models.CharField(max_length=50)
#     tags = ArrayField(models.CharField(max_length=200), blank=True, default=list)
#
#     objects = ProcessedModelManager()
#
#     class Meta:
#         db_table = 'processed_survey'
#
#
# class ProcessedScheduleManager(models.Manager):
#
#     def populate_from_unmanaged(self):
#         """Populates Schedule objects from unmanaged database"""
#         instances = Schedule.objects.all()
#         self.bulk_create(instances, ignore_conflicts=True)  # Bulk insert, avoiding duplicates
#
#
# class ProcessedScheduleModel(models.Model):
#     id = models.IntegerField(primary_key=True)
#     slug = models.CharField(max_length=255)
#     extracted_numbers = ArrayField(models.CharField(max_length=200,default=None), blank=True, default=list)
#     objects = ProcessedScheduleManager()
#
#     @classmethod
#     def with_extracted_numbers(cls) -> models.QuerySet:
#         """
#         Annotates each Schedule instance with an array of numbers extracted from `slug`
#         using PostgreSQL's `regexp_matches()`, ensuring rows with no matches are included.
#         """
#
#         class RegexpMatches(Func):
#             function = 'REGEXP_MATCHES'
#             arity = 2  # Requires two arguments (column, regex pattern)
#
#         extracted_numbers_subquery = (
#             cls.objects.filter(id=OuterRef("id"))
#             .annotate(matches=RegexpMatches("slug", Value(r"(\d+[dwmy])(?:-(\d+[dwmy]))*(?:-(.*))")))
#             .values("matches")  # Extract only the matches column
#         )
#
#         return cls.objects.annotate(
#             extracted_numbers=Coalesce(
#                 Subquery(extracted_numbers_subquery,
#                          output_field=ArrayField(models.CharField(max_length=255), default=list)),
#                 Value([])
#             ))
#
#     class Meta:
#         db_table = 'processed_schedule'