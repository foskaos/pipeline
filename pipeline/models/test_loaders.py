import pytest
from unittest.mock import patch, MagicMock
from django.db import transaction
from types import SimpleNamespace

from .analytics import AnalyticsScheduleWindow, AnalyticsSchedule, AnalyticsActivity
from .loaders import (
    FullLoadManager,
    IncrementalLoadManager,
    IncrementalTransformLoadManager,
    DataLoader,
    ScheduleWindowTransformer
)
from .staging import StagingScheduleModel, IncrementalLog


@pytest.mark.django_db
def test_full_load_manager():
    """Ensure FullLoadManager performs a full load correctly."""
    mock_data = [{'id': 1, 'slug': 'test-schedule'}]  # Ensure it's a list of dicts

    with patch('pipeline.models.staging.StagingScheduleModel.objects.all') as mock_all:
        mock_queryset = MagicMock()
        mock_queryset.values.return_value.iterator.return_value = iter(mock_data)  # Correct way to mock
        mock_all.return_value = mock_queryset

        manager = FullLoadManager(table_model=StagingScheduleModel)
        manager.model = StagingScheduleModel
        manager.populate_model()

        assert StagingScheduleModel.objects.count() == 1
        assert StagingScheduleModel.objects.first().slug == "test-schedule"


@pytest.mark.django_db
def test_incremental_load_manager():
    """Ensure IncrementalLoadManager only loads new records."""
    mock_data = {'id': 2, 'slug': 'new-schedule'}
    IncrementalLog.objects.create(schedule_id=1)

    with patch('pipeline.models.staging.StagingScheduleModel.objects.filter') as mock_filter:
        mock_queryset = MagicMock()
        mock_queryset.values.return_value = mock_queryset
        mock_queryset.order_by.return_value = mock_queryset
        mock_queryset.iterator.return_value = iter([mock_data])
        mock_filter.return_value = mock_queryset

        manager = IncrementalLoadManager(
            table_key='schedule_id',
            table_model=StagingScheduleModel,
            incremental_key='id',
            incremental_model=IncrementalLog
        )
        manager.model = StagingScheduleModel
        manager.populate_model()

        assert StagingScheduleModel.objects.count() == 1
        assert StagingScheduleModel.objects.first().id == 2


@pytest.mark.django_db
def test_incremental_transform_load_manager():
    """Ensure IncrementalTransformLoadManager applies transformations correctly."""
    mock_data = {'id': 3, 'slug': '7d-10d-post-op'}
    IncrementalLog.objects.create(schedule_id=2)
    AnalyticsSchedule.objects.create(id=3, slug='7d-10d-post-op')

    with patch('pipeline.models.analytics.AnalyticsSchedule.objects.filter') as mock_filter:
        mock_queryset = MagicMock()
        mock_queryset.values.return_value = mock_queryset
        mock_queryset.order_by.return_value = mock_queryset
        mock_queryset.iterator.return_value = iter([mock_data])
        mock_filter.return_value = mock_queryset

        manager = IncrementalTransformLoadManager(
            table_key='schedule_id',
            table_model=AnalyticsSchedule,
            incremental_key='id',
            incremental_model=IncrementalLog,
            transformer=ScheduleWindowTransformer()
        )
        manager.model = AnalyticsScheduleWindow
        manager.populate_model()

        staged = AnalyticsScheduleWindow.objects.first()
        assert staged.id == 3
        assert staged.schedule_milestone_slug == 'operation'
        assert staged.schedule_offset_start == 7
        assert staged.schedule_offset_end == 10


@pytest.mark.django_db
def test_data_loader_batch_loader():
    """Ensure DataLoader's batch_loader processes batches correctly
       and calls bulk_create the expected number of times.
    """
    mock_instance = {'id': 1, 'slug': 'test-schedule'}
    mock_related_fields = []
    mock_related_lookup = {}

    manager = DataLoader()
    manager.model = StagingScheduleModel

    counter = iter(range(1, 101))

    def mock_build_output_object(*args, **kwargs):
        return StagingScheduleModel(id=next(counter), slug='test-schedule')

    manager.build_output_object = MagicMock(side_effect=mock_build_output_object)

    with patch.object(manager.model.objects, 'bulk_create') as mock_bulk_create:
        with transaction.atomic():
            manager.batch_loader(10, mock_instance, iter([mock_instance] * 49), mock_related_lookup,
                                 mock_related_fields)

        assert mock_bulk_create.call_count == 5

        for call in mock_bulk_create.call_args_list:
            batch = call[0][0]
            assert len(batch) == 10


@pytest.mark.django_db
def test_data_loader_missing_relations():
    """Ensure missing foreign keys are handled gracefully."""

    mock_instance = {
        'id': 1,
        'schedule_id': 999,  # Non-existent schedule id
        'content_slug': 'ms',
    }

    mock_related_fields = [
        SimpleNamespace(name='schedule_id',
                        related_model=AnalyticsSchedule,
                        related_fields=[(None, 'id'), ],
                        many_to_many=False)
    ]
    mock_related_lookup = {'AnalyticsSchedule': {}}

    manager = DataLoader()
    manager.model = AnalyticsActivity

    with patch.object(manager.model.objects, "bulk_create") as mock_bulk_create:
        with transaction.atomic():
            manager.batch_loader(10, mock_instance, iter([]), mock_related_lookup, mock_related_fields)

        assert mock_bulk_create.call_count == 1

    assert AnalyticsActivity.objects.count() == 0
