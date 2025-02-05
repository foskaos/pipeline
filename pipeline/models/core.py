# This set of models represents the transactional database, and is unmanaged.
# The point of this is to provide a Django Native interface


from django.db import models
from django.contrib.postgres.fields import ArrayField


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


class Activity(ExternalDatabaseModel):
    id = models.IntegerField(primary_key=True)
    content_slug = models.CharField(max_length=255)
    schedule_id = models.IntegerField()

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
