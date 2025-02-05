import pytest
from django.db import connection

print('nested ct')
@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock(), connection.cursor() as cursor:
        cursor.execute('CREATE SCHEMA IF NOT EXISTS analytics;')
        cursor.execute('CREATE SCHEMA IF NOT EXISTS public;')