from pipeline.models.core import ExternalDatabaseModel

class MSKDatabaseRouter:
    """
    A router to ensure the external models use the 'msk_db' database by default.
    """

    def db_for_read(self, model, **hints):
        """Send read operations to 'msk_db' for ExternalDatabaseModel subclasses."""
        if issubclass(model, ExternalDatabaseModel):
            return "msk_db"
        return None

    def db_for_write(self, model, **hints):
        """Prevent any write operations on external models."""
        if issubclass(model, ExternalDatabaseModel):
            return "msk_db"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations only within the same database."""
        db_set = {"msk_db", "default"}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Prevent migrations for the external database."""
        if app_label == "msk_db":
            return False
        return None
