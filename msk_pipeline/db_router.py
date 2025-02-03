import logging
from pipeline.models.core import ExternalDatabaseModel
from pipeline.models.analytics import AnalyticsModel

logger = logging.getLogger(__name__)

class MSKDatabaseRouter:
    """
    A database router to direct different sets of models to different databases.
    """

    def db_for_read(self, model, **hints):
        """Send read operations to the correct database."""
        if issubclass(model, ExternalDatabaseModel):
            return "msk_db"
        elif issubclass(model, AnalyticsModel):
            return "analytics_db"
        return "default"

    def db_for_write(self, model, **hints):
        """Send write operations to the correct database."""
        if issubclass(model, ExternalDatabaseModel):
            return "msk_db"
        elif issubclass(model, AnalyticsModel):
            return "analytics_db"
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations only within the same database."""
        db_set = {"msk_db", "default", "analytics_db"}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, model=None, **hints):
        """Ensure migrations run on the correct database."""
        logger.debug(f"allow_migrate called with db={db}, app_label={app_label}, model_name={model_name}, model={model}")

        if model:
            if issubclass(model, ExternalDatabaseModel):
                return db == "msk_db"
            elif issubclass(model, AnalyticsModel):
                return db == "analytics_db"
            return db == "default"

        # If no model info is provided, default to safe behavior
        return db == "default"