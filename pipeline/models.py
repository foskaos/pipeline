from django.db import models

class ExternalDatabaseModel(models.Model):
    class Meta:
        abstract = True
        managed = False  # Ensures Django does not manage the table
        app_label = 'msk_db'

    def save(self, *args, **kwargs):
        raise NotImplementedError("This model is read-only.")

class Schedule(ExternalDatabaseModel):
    id = models.AutoField(primary_key=True)
    slug = models.CharField(max_length=255)

    class Meta:
        db_table = 'schedule'
        managed = False  # Ensures Django does not manage the table


class Activity(ExternalDatabaseModel):
    id = models.AutoField(primary_key=True)
    content_slug = models.CharField(max_length=255)
    schedule_id = models.ForeignKey(Schedule, on_delete=models.CASCADE, db_column='schedule_id', db_constraint=False)

    class Meta:
        db_table = 'activity'
        managed = False  # Ensures Django does not manage the table


class Device(ExternalDatabaseModel):
    id = models.AutoField(primary_key=True)
    platform = models.CharField(max_length=50)
    os_version = models.CharField(max_length=50)

    class Meta:
        db_table = 'device'
        managed = False  # Ensures Django does not manage the table


class Journey(ExternalDatabaseModel):
    id = models.AutoField(primary_key=True)
    abbreviation = models.CharField(max_length=255)
    joint_slug = models.CharField(max_length=255)

    class Meta:
        db_table = 'journey'
        managed = False  # Ensures Django does not manage the table


class JourneyActivity(ExternalDatabaseModel):
    journey_id = models.ForeignKey(Journey, on_delete=models.CASCADE, db_column='journey_id', db_constraint=False)
    activity_id = models.ForeignKey(Activity, on_delete=models.CASCADE, db_column='activity_id', db_constraint=False)

    class Meta:
        db_table = 'journey_activity'
        managed = False  # Ensures Django does not manage the table


class Patient(ExternalDatabaseModel):
    id = models.AutoField(primary_key=True)
    age_bracket = models.CharField(max_length=50)
    sex = models.CharField(max_length=50)
    hospital = models.CharField(max_length=50)

    class Meta:
        db_table = 'patient'
        managed = False  # Ensures Django does not manage the table


class PatientJourney(ExternalDatabaseModel):
    id = models.AutoField(primary_key=True)
    patient_id = models.ForeignKey(Patient, on_delete=models.CASCADE, db_column='patient_id', db_constraint=False)
    journey_id = models.ForeignKey(Journey, on_delete=models.CASCADE, db_column='journey_id', db_constraint=False)
    invitation_date = models.DateField()
    registration_date = models.DateField()
    operation_date = models.DateField()
    discharge_date = models.DateField()
    consent_date = models.DateField()
    clinician_id = models.IntegerField()

    class Meta:
        db_table = 'patient_journey'
        managed = False  # Ensures Django does not manage the table


class StepResult(ExternalDatabaseModel):
    patient_id = models.ForeignKey(Patient, on_delete=models.CASCADE, db_column='patient_id', db_constraint=False)
    date = models.DateField()
    value = models.CharField(max_length=255)

    class Meta:
        db_table = 'step_result'
        managed = False  # Ensures Django does not manage the table


class Survey(ExternalDatabaseModel):
    id = models.AutoField(primary_key=True)
    slug = models.CharField(max_length=255)
    version = models.CharField(max_length=50)
    tags = models.JSONField()

    class Meta:
        db_table = 'survey'
        managed = False  # Ensures Django does not manage the table


class SurveyResult(ExternalDatabaseModel):
    id = models.AutoField(primary_key=True)
    patient_journey_id = models.ForeignKey(PatientJourney, on_delete=models.CASCADE, db_column='patient_journey_id', db_constraint=False)
    survey_id = models.ForeignKey(Survey, on_delete=models.CASCADE, db_column='survey_id', db_constraint=False)
    activity_id = models.ForeignKey(Activity, on_delete=models.CASCADE, db_column='activity_id', db_constraint=False)
    device_id = models.ForeignKey(Device, on_delete=models.CASCADE, db_column='device_id', db_constraint=False)
    score_value = models.IntegerField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    class Meta:
        db_table = 'survey_result'
        managed = False  # Ensures Django does not manage the table

