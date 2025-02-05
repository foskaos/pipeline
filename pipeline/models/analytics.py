from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.db.models import Func, OuterRef, Subquery, Value, QuerySet, F
from django.db.models.functions import Coalesce
from .staging import (StagingScheduleModel, StagingJourneyModel, StagingPatientModel, StagingDeviceModel,
                      StagingActivityModel, StagingSurveyModel, StagingStepResultsModel, StagingJourneyActivityModel,
                      StagingPatientJourneyModel, StagingSurveyResultsModel)
from .loaders import FullLoadManager, IncrementalLoadManager,IncrementalTransformLoadManager,ScheduleWindowTransformer, FullLoadQueryManager


class AnalyticsModel(models.Model):
    class Meta:
        abstract = True
        app_label = "pipeline"


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
    schedule_window = models.IntegerField(null=True, default=0)


    class Meta:
        db_table = "incremental_log"

    def save(self, *args, **kwargs):
        self.id = 1  # Ensure the primary key is always 1
        super().save(*args, **kwargs)


class AnalyticsSchedule(AnalyticsModel):
    id = models.IntegerField(primary_key=True)
    slug = models.CharField(max_length=255)

    objects = IncrementalLoadManager(
        table_key='schedule_id',
        table_model=StagingScheduleModel,
        incremental_key='id',
        incremental_model=AnalyticsIncrementalLog,
    )

    class Meta:
        db_table = "schedule"


class AnalyticsPatient(AnalyticsModel):
    id = models.IntegerField(primary_key=True)
    age_bracket = models.CharField(max_length=255, blank=True, null=True)
    sex = models.CharField(max_length=255, blank=True, null=True)
    hospital = models.CharField(max_length=255, blank=True, null=True)
    objects = IncrementalLoadManager(
        table_key='patient_id',
        table_model=StagingPatientModel,
        incremental_key='id',
        incremental_model=AnalyticsIncrementalLog,
    )

    class Meta:
        db_table = "patient"


class AnalyticsActivity(AnalyticsModel):
    id = models.IntegerField(primary_key=True)
    content_slug = models.CharField(max_length=255, blank=True)
    schedule_id = models.ForeignKey(AnalyticsSchedule, db_column='schedule_id', on_delete=models.SET_NULL, null=True, blank=True, default=None)

    objects = IncrementalLoadManager(
        table_key='activity_id',
        table_model=StagingActivityModel,
        incremental_key='id',
        incremental_model=AnalyticsIncrementalLog,
    )

    class Meta:
        db_table = "activity"


class AnalyticsJourney(AnalyticsModel):
    id = models.IntegerField(primary_key=True)
    abbreviation = models.CharField(max_length=255,blank=True,null=True)
    joint_slug = models.CharField(max_length=255,blank=True,null=True)
    activities = models.ManyToManyField(AnalyticsActivity, through='AnalyticsJourneyActivity')

    objects = IncrementalLoadManager(
        table_key='journey_id',
        table_model=StagingJourneyModel,
        incremental_key='id',
        incremental_model=AnalyticsIncrementalLog,
    )

    class Meta:
        db_table = "journey"


class AnalyticsDevice(AnalyticsModel):
    id = models.IntegerField(primary_key=True)
    platform = models.CharField(max_length=50, blank=True)
    os_version = models.CharField(max_length=50, blank=True)

    objects = IncrementalLoadManager(
        table_key='device_id',
        table_model=StagingDeviceModel,
        incremental_key='id',
        incremental_model=AnalyticsIncrementalLog,
    )

    class Meta:
        db_table = "device"


class AnalyticsSurvey(AnalyticsModel):
    id = models.IntegerField(primary_key=True)
    slug = models.CharField(max_length=255, blank=True)
    version = models.CharField(max_length=50, blank=True)
    tags = ArrayField(models.CharField(max_length=200, blank=True), blank=True, default=list, null=True)

    objects = IncrementalLoadManager(
        table_key='survey_id',
        table_model=StagingSurveyModel,
        incremental_key='id',
        incremental_model=AnalyticsIncrementalLog,
    )

    class Meta:
        db_table = "survey"


class AnalyticsJourneyActivity(AnalyticsModel):
    journey_id = models.ForeignKey(AnalyticsJourney, db_column='journey_id', on_delete=models.SET_NULL, null=True, blank=True)
    activity_id = models.ForeignKey(AnalyticsActivity, db_column='activity_id', on_delete=models.SET_NULL, null=True, blank=True)
    objects = FullLoadManager(table_model=StagingJourneyActivityModel)

    class Meta:
        db_table = "journey_activity"


class AnalyticsPatientJourney(AnalyticsModel):
    id = models.IntegerField(primary_key=True)
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
        db_table = "patient_journey"


class AnalyticsStepResults(AnalyticsModel):
    patient_id = models.ForeignKey(AnalyticsPatient, db_column='patient_id', on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    value = models.IntegerField()

    objects = IncrementalLoadManager(
        table_key='step_result_date',
        table_model=StagingStepResultsModel,
        incremental_key='date',
        incremental_model=AnalyticsIncrementalLog,
    )

    class Meta:
        db_table = "step_results"


class AnalyticsSurveyResults(AnalyticsModel):
    id = models.IntegerField(primary_key=True)
    patient_journey_id = models.ForeignKey(AnalyticsPatientJourney, db_column='patient_journey_id', on_delete=models.SET_NULL, null=True, blank=True)
    survey_id = models.ForeignKey(AnalyticsSurvey, db_column='survey_id', on_delete=models.SET_NULL, null=True, blank=True)
    activity_id = models.ForeignKey(AnalyticsActivity, db_column='activity_id', on_delete=models.SET_NULL, null=True, blank=True)
    device_id = models.ForeignKey(AnalyticsDevice,db_column='device_id', on_delete=models.SET_NULL, null=True, blank=True)
    score_value = models.IntegerField(blank=True, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    objects = FullLoadManager(table_model=StagingSurveyResultsModel)

    class Meta:
        db_table = "survey_results"


class AnalyticsScheduleWindow(AnalyticsModel):
    id = models.AutoField(primary_key=True)
    schedule = models.OneToOneField(
        AnalyticsSchedule,
        on_delete=models.CASCADE,
        related_name='schedule_window'
    )
    schedule_milestone_slug = models.CharField(max_length=255)
    schedule_offset_start = models.IntegerField()
    # allowing for null end offset where the schedule is of indefinite length
    schedule_offset_end = models.IntegerField(blank=True, null=True)

    objects = IncrementalTransformLoadManager(
        table_key='schedule_window',
        table_model=AnalyticsSchedule,
        incremental_key='id',
        incremental_model=AnalyticsIncrementalLog,
        transformer=ScheduleWindowTransformer()
        )

    class Meta:
        db_table = "schedule_window"


class AnalyticsPatientJourneyScheduleWindow(AnalyticsModel):
    id = models.AutoField(primary_key=True)
    patient_id = models.ForeignKey(AnalyticsPatient, db_column='patient_id', on_delete=models.SET_NULL, null=True, blank=True)
    patient_journey_id = models.ForeignKey(AnalyticsPatientJourney, db_column='patient_journey_id',on_delete=models.SET_NULL, null=True, blank=True)
    activity_id = models.ForeignKey(AnalyticsActivity, db_column='activity_id', on_delete=models.SET_NULL, null=True, blank=True)
    activity_content_slug = models.CharField(max_length=255, blank=True, null=True)
    schedule_id = models.ForeignKey(AnalyticsSchedule, db_column='schedule_id', on_delete=models.SET_NULL, null=True, blank=True)
    schedule_slug = models.CharField(max_length=255, blank=True, null=True)
    schedule_start_offset_days = models.IntegerField(blank=True, null=True)
    schedule_end_offset_days = models.IntegerField(blank=True, null=True)
    schedule_milestone_slug = models.CharField(max_length=255, blank=True, null=True)

    @staticmethod
    def loader_query():
        return AnalyticsPatientJourney.objects.annotate(
            # Rename the patient journey’s id so we have a patient_journey_id column
            patient_journey_id=F('id'),
            # From the journey (FK field named `journey_id` on AnalyticsPatientJourney)
            # traverse the many-to-many to get the activity id
            activity_id=F('journey_id__activities__id'),
            activity_content_slug=F('journey_id__activities__content_slug'),
            # the schedule id is on the activity
            schedule_id=F('journey_id__activities__schedule_id'),
            schedule_slug=F('journey_id__activities__schedule_id__slug'),
            # From the schedule, follow the one-to-one relation to its schedule window
            schedule_start_offset_days=F('journey_id__activities__schedule_id__schedule_window__schedule_offset_start'),
            schedule_end_offset_days=F('journey_id__activities__schedule_id__schedule_window__schedule_offset_end'),
            schedule_milestone_slug=F('journey_id__activities__schedule_id__schedule_window__schedule_milestone_slug')
        ).values(
            'patient_id',  # AnalyticsPatientJourney.patient_id (FK)
            'patient_journey_id',  # the annotated primary key of the journey record
            'activity_id',  # id from AnalyticsActivity
            'activity_content_slug',
            'schedule_id',  # id from AnalyticsSchedule (on the Activity)
            'schedule_slug',
            'schedule_start_offset_days',  # from AnalyticsScheduleWindow
            'schedule_end_offset_days',  # from AnalyticsScheduleWindow
            'schedule_milestone_slug'  # using the schedule_window’s milestone slug field
        ).iterator()

    objects = FullLoadQueryManager(table_model=AnalyticsPatientJourney,
                                   query=loader_query)


    class Meta:
        db_table = "patient_journey_schedule_window"

analytics_pipeline = [
    AnalyticsSchedule,
    AnalyticsScheduleWindow,
    AnalyticsJourney,
    AnalyticsPatient,
    AnalyticsDevice,
    AnalyticsActivity,
    AnalyticsSurvey,
    # AnalyticsStepResults,
    AnalyticsJourneyActivity,
    AnalyticsPatientJourney,
    AnalyticsSurveyResults,
    AnalyticsPatientJourneyScheduleWindow
]