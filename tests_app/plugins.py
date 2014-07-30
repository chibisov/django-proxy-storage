# -*- coding: utf-8 -*-
import os

from django_nose.plugin import AlwaysOnPlugin

from django.test import TestCase
from django.core.cache import cache
from django.conf import settings

from pymongo import MongoClient
import shutil


class UnitTestDiscoveryPlugin(AlwaysOnPlugin):
    """
    Enables unittest compatibility mode (dont test functions, only TestCase
    subclasses, and only methods that start with [Tt]est).
    """
    enabled = True

    def wantModule(self, module):
        return True

    def wantFile(self, file):
        if file.endswith('.py'):
            return True

    def wantClass(self, cls):
        if not issubclass(cls, TestCase):
            return False

    def wantMethod(self, method):
        if not method.__name__.lower().startswith('test'):
            return False

    def wantFunction(self, function):
        return False


class FlushCache(AlwaysOnPlugin):
    # startTest didn't work :(
    def begin(self):
        self._monkeypatch_testcase()

    def _monkeypatch_testcase(self):
        old_run = TestCase.run
        def new_run(*args, **kwargs):
            cache.clear()
            return old_run(*args, **kwargs)
        TestCase.run = new_run


class FlushTempDir(AlwaysOnPlugin):
    def finalize(self, result):
        shutil.rmtree(settings.TEMP_DIR, ignore_errors=True)


class FlushMongo(AlwaysOnPlugin):
    def begin(self):
        self.remove_all_test_databases()

    def remove_all_test_databases(self):
        mongo_db = MongoClient('localhost', settings.MONGO_DATABASE_PORT)
        for database_name in mongo_db.database_names():
            if database_name.startswith(settings.MONGO_TEST_DATABASE_PREFIX):
                mongo_db.drop_database(database_name)

    def startTest(self, test):
        db = MongoClient('localhost', settings.MONGO_DATABASE_PORT)[settings.MONGO_DATABASE_NAME]
        for collection_name in db.collection_names():
            if collection_name != 'system.indexes':
                getattr(db, collection_name).remove({})