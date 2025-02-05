
from django.core.management import call_command
from django.test import TestCase
from unittest.mock import patch, MagicMock

from pipeline.management.commands.run_pipeline import execute_pipeline
from pipeline.models.staging import StagingScheduleModel, StagingJourneyModel, StagingPatientModel, StagingDeviceModel, StagingActivityModel, StagingSurveyModel,  StagingStepResultsModel, StagingJourneyActivityModel, StagingPatientJourneyModel, StagingSurveyResultsModel, staging_pipeline
from pipeline.models.analytics import AnalyticsSchedule, AnalyticsScheduleWindow, AnalyticsJourney, AnalyticsPatient, AnalyticsDevice, AnalyticsActivity, AnalyticsSurvey,  AnalyticsStepResults, AnalyticsJourneyActivity, AnalyticsPatientJourney, AnalyticsSurveyResults, AnalyticsPatientJourneyScheduleWindow, analytics_pipeline


intended_staging_pipeline = [StagingScheduleModel, StagingJourneyModel, StagingPatientModel, StagingDeviceModel, StagingActivityModel, StagingSurveyModel, StagingStepResultsModel, StagingJourneyActivityModel, StagingPatientJourneyModel, StagingSurveyResultsModel]
intended_analytics_pipeline = [AnalyticsSchedule, AnalyticsScheduleWindow, AnalyticsJourney, AnalyticsPatient, AnalyticsDevice, AnalyticsActivity, AnalyticsSurvey,  AnalyticsStepResults, AnalyticsJourneyActivity, AnalyticsPatientJourney, AnalyticsSurveyResults, AnalyticsPatientJourneyScheduleWindow]

class RunPipelineCommandTest(TestCase):

    @patch('pipeline.management.commands.run_pipeline.execute_pipeline')
    def test_pipeline_runs_both_pipelines_by_default(self, mock_execute_pipeline):
        """Test that both staging and analytics pipelines run by default"""
        mock_execute_pipeline.return_value = {}

        call_command("run_pipeline")

        # Ensure execute_pipeline is called with both pipelines
        mock_execute_pipeline.assert_any_call(staging_pipeline)
        mock_execute_pipeline.assert_any_call(analytics_pipeline)
        assert mock_execute_pipeline.call_count == 2

    @patch('pipeline.models.staging.staging_pipeline', new_callable=lambda: list(intended_staging_pipeline))
    def test_staging_pipeline_models_called(self, mock_pipeline):
        """Test that each model in staging_pipeline calls populate_model"""

        mock_models = [MagicMock(__name__=model.__name__) for model in mock_pipeline]

        for mock_model in mock_models:
            mock_model.objects.populate_model.return_value = "Success"

        mock_pipeline.clear()
        mock_pipeline.extend(mock_models)

        result = execute_pipeline(mock_pipeline)

        # Ensure populate_model was called for each model
        for mock_model in mock_models:
            mock_model.objects.populate_model.assert_called_once()

        # Check the returned analytics log contains expected results
        expected_log = {mock_model.__name__: "Success" for mock_model in mock_models}

        assert result == expected_log

    @patch('pipeline.models.analytics.analytics_pipeline', new_callable=lambda: list(intended_analytics_pipeline))
    def test_analytics_pipeline_models_called(self, mock_pipeline):
        """Test that each model in staging_pipeline calls populate_model"""

        mock_models = [MagicMock(__name__=model.__name__) for model in mock_pipeline]

        for mock_model in mock_models:
            mock_model.objects.populate_model.return_value = "Success"

        mock_pipeline.clear()
        mock_pipeline.extend(mock_models)

        result = execute_pipeline(mock_pipeline)

        # Ensure populate_model was called for each model
        for mock_model in mock_models:
            mock_model.objects.populate_model.assert_called_once()

        # Check the returned analytics log contains expected results
        expected_log = {mock_model.__name__: "Success" for mock_model in mock_models}

        assert result == expected_log