# Generated by Django 5.1.5 on 2025-02-02 18:56

import django.contrib.postgres.fields
import django.db.models.manager
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('content_slug', models.CharField(max_length=255)),
                ('schedule_id', models.IntegerField()),
            ],
            options={
                'db_table': 'activity',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('platform', models.CharField(max_length=50)),
                ('os_version', models.CharField(max_length=50)),
            ],
            options={
                'db_table': 'device',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Journey',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('abbreviation', models.CharField(max_length=255)),
                ('joint_slug', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'journey',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='JourneyActivity',
            fields=[
                ('journey_id', models.IntegerField(primary_key=True, serialize=False)),
                ('activity_id', models.IntegerField()),
            ],
            options={
                'db_table': 'journey_activity',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('age_bracket', models.CharField(max_length=50)),
                ('sex', models.CharField(max_length=50)),
                ('hospital', models.CharField(max_length=50)),
            ],
            options={
                'db_table': 'patient',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='PatientJourney',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('invitation_date', models.DateField()),
                ('registration_date', models.DateField()),
                ('operation_date', models.DateField()),
                ('discharge_date', models.DateField()),
                ('consent_date', models.DateField()),
                ('clinician_id', models.IntegerField()),
            ],
            options={
                'db_table': 'patient_journey',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Schedule',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('slug', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'schedule',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='StepResult',
            fields=[
                ('patient_id', models.IntegerField(primary_key=True, serialize=False)),
                ('date', models.DateField()),
                ('value', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'step_result',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Survey',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('slug', models.CharField(max_length=255)),
                ('version', models.CharField(max_length=50)),
                ('tags', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=200), blank=True, size=None)),
            ],
            options={
                'db_table': 'survey',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='SurveyResult',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('score_value', models.IntegerField()),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
            ],
            options={
                'db_table': 'survey_result',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='IncrementalLog',
            fields=[
                ('id', models.IntegerField(default=1, primary_key=True, serialize=False)),
                ('schedule_id', models.IntegerField(default=0)),
                ('journey_id', models.IntegerField(default=0)),
                ('activity_id', models.IntegerField(default=0)),
                ('patient_id', models.IntegerField(default=0)),
                ('device_id', models.IntegerField(default=0)),
                ('survey_id', models.IntegerField(default=0)),
                ('step_result_date', models.DateField(null=True)),
            ],
            options={
                'db_table': 'staging_incremental_log',
            },
        ),
        migrations.CreateModel(
            name='StagingActivityModel',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('content_slug', models.CharField(blank=True, max_length=255)),
                ('schedule_id', models.IntegerField(blank=True)),
            ],
            options={
                'db_table': 'staging_activity',
            },
            managers=[
                ('StagingActivityManager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='StagingDeviceModel',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('platform', models.CharField(blank=True, max_length=50)),
                ('os_version', models.CharField(blank=True, max_length=50)),
            ],
            options={
                'db_table': 'staging_device',
            },
            managers=[
                ('StagingDeviceManager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='StagingJourneyActivityModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('journey_id', models.IntegerField()),
                ('activity_id', models.IntegerField()),
            ],
            options={
                'db_table': 'staging_journey_activity',
            },
            managers=[
                ('StagingJourneyActivityManager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='StagingJourneyModel',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('abbreviation', models.CharField(blank=True, max_length=255, null=True)),
                ('joint_slug', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'db_table': 'staging_journey',
            },
            managers=[
                ('StagingJourneyManager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='StagingPatientJourneyModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('patient_id', models.IntegerField()),
                ('journey_id', models.IntegerField()),
                ('invitation_date', models.DateField(blank=True, null=True)),
                ('registration_date', models.DateField(blank=True, null=True)),
                ('operation_date', models.DateField(blank=True, null=True)),
                ('discharge_date', models.DateField(blank=True, null=True)),
                ('consent_date', models.DateField(blank=True, null=True)),
                ('clinician_id', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'db_table': 'staging_patient_journey',
            },
            managers=[
                ('StagingPatientJourneyManager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='StagingPatientModel',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('age_bracket', models.CharField(blank=True, max_length=255, null=True)),
                ('sex', models.CharField(blank=True, max_length=255, null=True)),
                ('hospital', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'db_table': 'staging_patient',
            },
            managers=[
                ('StagingPatientManager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='StagingScheduleModel',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('slug', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'staging_schedule',
            },
            managers=[
                ('StagingScheduleManager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='StagingStepResultsModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('patient_id', models.IntegerField()),
                ('date', models.DateField()),
                ('value', models.IntegerField()),
            ],
            options={
                'db_table': 'staging_step_results',
            },
            managers=[
                ('StagingStepResultsManager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='StagingSurveyModel',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('slug', models.CharField(blank=True, max_length=255)),
                ('version', models.CharField(blank=True, max_length=50)),
                ('tags', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=200), blank=True, default=list, null=True, size=None)),
            ],
            options={
                'db_table': 'staging_survey',
            },
            managers=[
                ('StagingSurveyManager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='StagingSurveyResultsModel',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('patient_journey_id', models.IntegerField()),
                ('survey_id', models.IntegerField()),
                ('activity_id', models.IntegerField()),
                ('device_id', models.IntegerField()),
                ('score_value', models.IntegerField(blank=True, null=True)),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
            ],
            options={
                'db_table': 'staging_survey_results',
            },
            managers=[
                ('StagingSurveyResultsManger', django.db.models.manager.Manager()),
            ],
        ),
    ]
