from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.db.models import Func, OuterRef, Subquery, Value, QuerySet
from django.db.models.functions import Coalesce
from .staging import (StagingScheduleModel, StagingJourneyModel, StagingPatientModel, StagingDeviceModel,
                      StagingActivityModel, StagingSurveyModel, StagingStepResultsModel, StagingJourneyActivityModel,
                      StagingPatientJourneyModel, StagingSurveyResultsModel)
from .loaders import FullLoadManager, IncrementalManager


class AnalyticsModel(models.Model):
    class Meta:
        abstract = True
        app_label = "analytics_db"


class AnalyticsIncrementalLog(AnalyticsModel):
    # We force the ID to always be 1 so there can be only one row.
    id = models.IntegerField(primary_key=True, default=1)
    schedule_id = models.IntegerField(default=0)
    journey_id = models.IntegerField(default=0)
    activity_id = models.IntegerField(default=0)
    patient_id = models.IntegerField(default=0)
    device_id = models.IntegerField(default=0)
    survey_id = models.IntegerField(default=0)
    step_result_date = models.DateField(null=True)

    class Meta:
        db_table = 'incremental_log'

    def save(self, *args, **kwargs):
        self.id = 1  # Ensure the primary key is always 1
        super().save(*args, **kwargs)


class AnalyticsSchedule(AnalyticsModel):
    id = models.IntegerField(primary_key=True)
    slug = models.CharField(max_length=255)
    # extracted_numbers = ArrayField(models.CharField(max_length=200,default=None), blank=True, default=list)

    objects = IncrementalManager(
        table_key='schedule_id',
        table_model=StagingScheduleModel,
        incremental_key='id',
        incremental_model=AnalyticsIncrementalLog,
    )

    class Meta:
        db_table = 'schedule'


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


class AnalyticsPatient(AnalyticsModel):
    id = models.IntegerField(primary_key=True)
    age_bracket = models.CharField(max_length=255, blank=True, null=True)
    sex = models.CharField(max_length=255, blank=True, null=True)
    hospital = models.CharField(max_length=255, blank=True, null=True)
    objects = IncrementalManager(
        table_key='patient_id',
        table_model=StagingPatientModel,
        incremental_key='id',
        incremental_model=AnalyticsIncrementalLog,
    )

    class Meta:
        db_table = 'patient'


class AnalyticsActivity(AnalyticsModel):
    id = models.IntegerField(primary_key=True)
    content_slug = models.CharField(max_length=255, blank=True)
    schedule_id = models.ForeignKey(AnalyticsSchedule, db_column='schedule_id', on_delete=models.SET_NULL, null=True, blank=True, default=None)

    objects = IncrementalManager(
        table_key='activity_id',
        table_model=StagingActivityModel,
        incremental_key='id',
        incremental_model=AnalyticsIncrementalLog,
    )
    class Meta:
        db_table = 'activity'


class AnalyticsJourney(AnalyticsModel):
    id = models.IntegerField(primary_key=True)
    abbreviation = models.CharField(max_length=255,blank=True,null=True)
    joint_slug = models.CharField(max_length=255,blank=True,null=True)

    objects = IncrementalManager(
        table_key='journey_id',
        table_model=StagingJourneyModel,
        incremental_key='id',
        incremental_model=AnalyticsIncrementalLog,
    )

    class Meta:
        db_table = 'journey'


class AnalyticsDevice(AnalyticsModel):
    id = models.IntegerField(primary_key=True)
    platform = models.CharField(max_length=50, blank=True)
    os_version = models.CharField(max_length=50, blank=True)

    objects = IncrementalManager(
        table_key='device_id',
        table_model=StagingDeviceModel,
        incremental_key='id',
        incremental_model=AnalyticsIncrementalLog,
    )

    class Meta:
        db_table = 'device'


class AnalyticsSurvey(AnalyticsModel):
    id = models.IntegerField(primary_key=True)
    slug = models.CharField(max_length=255, blank=True)
    version = models.CharField(max_length=50, blank=True)
    tags = ArrayField(models.CharField(max_length=200, blank=True), blank=True, default=list, null=True)

    objects = IncrementalManager(
        table_key='survey_id',
        table_model=StagingSurveyModel,
        incremental_key='id',
        incremental_model=AnalyticsIncrementalLog,
    )

    class Meta:
        db_table = 'survey'


class AnalyticsJourneyActivity(AnalyticsModel):
    journey_id = models.ForeignKey(AnalyticsJourney, db_column='journey_id', on_delete=models.SET_NULL, null=True, blank=True)
    activity_id = models.ForeignKey(AnalyticsActivity, db_column='activity_id', on_delete=models.SET_NULL, null=True, blank=True)
    objects = FullLoadManager(table_model=StagingJourneyActivityModel)
    class Meta:
        db_table = 'journey_activity'


class AnalyticsPatientJourney(AnalyticsModel):
    patient_id = models.ForeignKey(AnalyticsPatient, db_column='patient_id', on_delete=models.SET_NULL, null=True, blank=True)
    journey_id = models.ForeignKey(AnalyticsJourney, db_column='journey_id', on_delete=models.SET_NULL, null=True, blank=True)
    invitation_date = models.DateField(null=True, blank=True)
    registration_date = models.DateField(null=True, blank=True)
    operation_date = models.DateField(null=True, blank=True)
    discharge_date = models.DateField(null=True, blank=True)
    consent_date = models.DateField(null=True, blank=True)
    clinician_id = models.IntegerField(null=True, blank=True)
    objects = FullLoadManager(table_model=StagingPatientJourneyModel)


    class Meta:
        db_table = 'patient_journey'


class AnalyticsStepResults(AnalyticsModel):
    patient_id = models.ForeignKey(AnalyticsPatient, db_column='patient_id', on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    value = models.IntegerField()

    objects = IncrementalManager(
        table_key='step_result_date',
        table_model=StagingStepResultsModel,
        incremental_key='data',
        incremental_model=AnalyticsIncrementalLog,
    )

    class Meta:
        db_table = 'step_results'


class AnalyticsSurveyResults(AnalyticsModel):
    id = models.IntegerField(primary_key=True)
    patient_journey_id = models.ForeignKey(AnalyticsPatientJourney, db_column='patient_journey_id', on_delete=models.SET_NULL, null=True, blank=True)
    survey_id = models.ForeignKey(AnalyticsSurvey, db_column='survey_id', on_delete=models.SET_NULL, null=True, blank=True)
    activity_id = models.ForeignKey(AnalyticsActivity, db_column='activity_id', on_delete=models.SET_NULL, null=True, blank=True)
    device_id = models.ForeignKey(AnalyticsDevice,db_column='device_id', on_delete=models.SET_NULL, null=True, blank=True)
    score_value = models.IntegerField(blank=True, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    StagingSurveyResultsManger = FullLoadManager(table_model=StagingSurveyResultsModel)

    class Meta:
        db_table = 'survey_results'


analytics_pipeline = [
    AnalyticsSchedule,
    AnalyticsJourney,
    AnalyticsPatient,
    # AnalyticsDevice,
    # AnalyticsActivity,
    # AnalyticsSurvey,
    # AnalyticsStepResults,
    # AnalyticsJourneyActivity,
    # AnalyticsPatientJourney,
    # AnalyticsSurveyResults,
]