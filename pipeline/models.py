# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Activity(models.Model):
    content_slug = models.CharField(max_length=255, blank=True, null=True)
    schedule_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'activity'


class Device(models.Model):
    platform = models.CharField(max_length=50, blank=True, null=True)
    os_version = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'device'


class Journey(models.Model):
    abbreviation = models.CharField(max_length=255, blank=True, null=True)
    joint_slug = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'journey'


class JourneyActivity(models.Model):
    journey_id = models.IntegerField(primary_key=True)  # The composite primary key (journey_id, activity_id) found, that is not supported. The first column is selected.
    activity_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'journey_activity'
        unique_together = (('journey_id', 'activity_id'),)


class Patient(models.Model):
    age_bracket = models.CharField(max_length=50, blank=True, null=True)
    sex = models.CharField(max_length=50, blank=True, null=True)
    hospital = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'patient'


class PatientJourney(models.Model):
    patient_id = models.IntegerField(blank=True, null=True)
    journey_id = models.IntegerField(blank=True, null=True)
    invitation_date = models.DateField(blank=True, null=True)
    registration_date = models.DateField(blank=True, null=True)
    operation_date = models.DateField(blank=True, null=True)
    discharge_date = models.DateField(blank=True, null=True)
    consent_date = models.DateField(blank=True, null=True)
    clinician_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'patient_journey'


class Schedule(models.Model):
    slug = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'schedule'


class StepResult(models.Model):
    patient_id = models.IntegerField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    value = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'step_result'


class Survey(models.Model):
    slug = models.CharField(max_length=255, blank=True, null=True)
    version = models.CharField(max_length=50, blank=True, null=True)
    tags = models.TextField(blank=True, null=True)  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'survey'


class SurveyResult(models.Model):
    patient_journey_id = models.IntegerField(blank=True, null=True)
    survey_id = models.IntegerField(blank=True, null=True)
    activity_id = models.IntegerField(blank=True, null=True)
    device_id = models.IntegerField(blank=True, null=True)
    score_value = models.IntegerField(blank=True, null=True)
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'survey_result'
