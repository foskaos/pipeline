# These models actually extract data from the database and are managed by django orm
# This model is designed to extract the data without distrubing the transactional db too much
# Incremental loading is preferred to minimize the queries on the transactional db.


from django.db import models, transaction
from django.contrib.postgres.fields import ArrayField
from django.db.models import Func, OuterRef, Subquery, Value, QuerySet, Field
from django.db.models.functions import Coalesce
from .core import Schedule, Journey, Activity, Patient, Device, Survey, JourneyActivity, PatientJourney, StepResult, \
    SurveyResult
import datetime
from typing import Iterable
from .loaders import IncrementalLoadManager, FullLoadManager


class IncrementalLog(models.Model):
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
        db_table = "staging_incremental_log"

    def save(self, *args, **kwargs):
        self.id = 1
        super().save(*args, **kwargs)


class StagingScheduleModel(models.Model):
    id = models.IntegerField(primary_key=True)
    slug = models.CharField(max_length=255)
    StagingScheduleManager = IncrementalLoadManager(table_key='schedule_id',
                                                    table_model=Schedule,
                                                    incremental_key='id',
                                                    incremental_model=IncrementalLog)
    objects = StagingScheduleManager

    class Meta:
        db_table = "staging_schedule"



class StagingPatientModel(models.Model):
    id = models.IntegerField(primary_key=True)
    age_bracket = models.CharField(max_length=255, blank=True, null=True)
    sex = models.CharField(max_length=255, blank=True, null=True)
    hospital = models.CharField(max_length=255, blank=True, null=True)

    StagingPatientManager = IncrementalLoadManager(table_key='patient_id',
                                                   table_model=Patient,
                                                   incremental_key='id',
                                                   incremental_model=IncrementalLog)

    objects = StagingPatientManager

    class Meta:
        db_table = "staging_patient"


class StagingActivityModel(models.Model):
    id = models.IntegerField(primary_key=True)
    content_slug = models.CharField(max_length=255, blank=True)
    schedule_id = models.IntegerField(blank=True)

    StagingActivityManager = IncrementalLoadManager(table_key='activity_id',
                                                    table_model=Activity,
                                                    incremental_key='id',
                                                    incremental_model=IncrementalLog)

    objects = StagingActivityManager

    class Meta:
        db_table = "staging_activity"


class StagingJourneyModel(models.Model):
    id = models.IntegerField(primary_key=True)
    abbreviation = models.CharField(max_length=255, blank=True, null=True)
    joint_slug = models.CharField(max_length=255, blank=True, null=True)

    StagingJourneyManager = IncrementalLoadManager(table_key='journey_id',
                                                   table_model=Journey,
                                                   incremental_key='id',
                                                   incremental_model=IncrementalLog)

    objects = StagingJourneyManager

    class Meta:
        db_table = "staging_journey"


class StagingDeviceModel(models.Model):
    "full load"
    id = models.IntegerField(primary_key=True)
    platform = models.CharField(max_length=50, blank=True)
    os_version = models.CharField(max_length=50, blank=True)

    StagingDeviceManager = IncrementalLoadManager(table_key='device_id',
                                                  table_model=Device,
                                                  incremental_key='id',
                                                  incremental_model=IncrementalLog)
    objects = StagingDeviceManager

    class Meta:
        db_table = "staging_device"


class StagingSurveyModel(models.Model):
    id = models.IntegerField(primary_key=True)
    slug = models.CharField(max_length=255, blank=True)
    version = models.CharField(max_length=50, blank=True)
    tags = ArrayField(models.CharField(max_length=200, blank=True), blank=True, default=list, null=True)

    StagingSurveyManager = IncrementalLoadManager(table_key='survey_id',
                                                  table_model=Survey,
                                                  incremental_key='id',
                                                  incremental_model=IncrementalLog)

    objects = StagingSurveyManager

    class Meta:
        db_table = "staging_survey"


class StagingJourneyActivityModel(models.Model):
    journey_id = models.IntegerField()
    activity_id = models.IntegerField()

    StagingJourneyActivityManager = FullLoadManager(table_model=JourneyActivity)
    objects = StagingJourneyActivityManager

    class Meta:
        db_table = "staging_journey_activity"


class StagingPatientJourneyModel(models.Model):
    id = models.IntegerField(primary_key=True)
    patient_id = models.IntegerField()
    journey_id = models.IntegerField()
    invitation_date = models.DateField(null=True, blank=True)
    registration_date = models.DateField(null=True, blank=True)
    operation_date = models.DateField(null=True, blank=True)
    discharge_date = models.DateField(null=True, blank=True)
    consent_date = models.DateField(null=True, blank=True)
    clinician_id = models.IntegerField(null=True, blank=True)

    StagingPatientJourneyManager = FullLoadManager(table_model=PatientJourney)
    objects = StagingPatientJourneyManager

    class Meta:
        db_table = "staging_patient_journey"


class StagingStepResultsModel(models.Model):
    patient_id = models.IntegerField()
    date = models.DateField()
    value = models.IntegerField()

    StagingStepResultsManager = IncrementalLoadManager(
        table_key='step_result_date',
        table_model=StepResult,
        incremental_key='date',
        incremental_model=IncrementalLog)

    objects = StagingStepResultsManager

    class Meta:
        db_table = "staging_step_results"


class StagingSurveyResultsModel(models.Model):
    id = models.IntegerField(primary_key=True)
    patient_journey_id = models.IntegerField()
    survey_id = models.IntegerField()
    activity_id = models.IntegerField()
    device_id = models.IntegerField()
    score_value = models.IntegerField(blank=True, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    StagingSurveyResultsManger = FullLoadManager(table_model=SurveyResult)
    objects = StagingSurveyResultsManger

    class Meta:
        db_table = "staging_survey_results"


staging_pipeline = [
    StagingScheduleModel,
    StagingJourneyModel,
    StagingPatientModel,
    StagingDeviceModel,
    StagingActivityModel,
    StagingSurveyModel,
    StagingStepResultsModel,
    StagingJourneyActivityModel,
    StagingPatientJourneyModel,
    StagingSurveyResultsModel
]
