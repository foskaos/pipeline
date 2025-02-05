from unittest.mock import patch, MagicMock

import pytest
from django.db.utils import IntegrityError

from .core import Schedule, Activity, Patient
from .staging import StagingPatientModel, StagingScheduleModel, IncrementalLog
from .analytics import AnalyticsSchedule
from .loaders import ScheduleWindowTransformer


@pytest.mark.django_db()
def test_core_models_are_readonly():
    """Test ExternalDatabaseModel prevents writes"""
    models_to_test = [
        (Schedule, {'id': 1, 'slug': 'test-schedule'}),
        (Activity, {'id': 1, 'content_slug': 'test-activity', 'schedule_id': 1}),
        (Patient, {'id': 1, 'age_bracket': 'Adult', 'sex': 'M', 'hospital': 'Test'})
    ]

    for model, test_data in models_to_test:
        with pytest.raises(NotImplementedError, match="This model is read-only."):
            model.objects.create(**test_data)

        instance = model(**test_data)
        with pytest.raises(NotImplementedError, match="This model is read-only."):
            instance.save()


@pytest.mark.django_db
def test_incremental_log_defaults():
    """Ensure the IncrementalLog is correctly initialized with default values."""
    log = IncrementalLog.objects.create()
    assert log.id == 1
    assert log.schedule_id == 0
    assert log.patient_id == 0
    assert log.step_result_date is None


@pytest.mark.django_db(databases=['msk_db', 'default'])
def test_staging_models_incremental_load():
    """tests incremental loading"""
    mock_data = {
        'id': 1,
        'age_bracket': "Adult",
        'sex': "M",
        'hospital': "General"
    }

    with patch('pipeline.models.core.Patient.objects') as mock_objects:
        mock_queryset = MagicMock()
        mock_queryset.values.return_value = mock_queryset
        mock_queryset.order_by.return_value = mock_queryset
        mock_queryset.iterator.return_value = iter([mock_data])
        mock_objects.all.return_value = mock_queryset

        StagingPatientModel.objects.populate_model()

        assert StagingPatientModel.objects.count() == 1
        staged_patient = StagingPatientModel.objects.first()
        assert staged_patient.age_bracket == "Adult"
        assert staged_patient.sex == "M"
        assert staged_patient.hospital == "General"


@pytest.mark.django_db
def test_analytics_models_linked_properly():
    """Ensure analytics models link correctly with staging data."""
    schedule = StagingScheduleModel.objects.create(id=1, slug="test")
    AnalyticsSchedule.objects.populate_model()

    assert AnalyticsSchedule.objects.count() == 1
    assert AnalyticsSchedule.objects.first().slug == "test"


@pytest.mark.django_db
def test_schedule_window_transformer():
    """Ensure slug transformation is working as expected."""
    slug = "7d-op"
    transformed = ScheduleWindowTransformer.process_slug(slug)

    assert transformed["schedule_offset_start"] == 7
    assert transformed["schedule_milestone_slug"] == "operation"
