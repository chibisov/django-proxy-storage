# -*- coding: utf-8 -*-
import tempfile
import shutil
import os

from pymongo import MongoClient

from django.core.files.storage import FileSystemStorage
from django.test import TestCase
from django.conf import settings
from django.core.files.base import ContentFile

from proxy_storage.meta_backends.orm import ORMMetaBackend
from proxy_storage.meta_backends.mongo import MongoMetaBackend
from proxy_storage.storages.base import ProxyStorageBase
from proxy_storage.testutils import create_test_cases_for_proxy_storage

from tests_app.models import (
    ProxyStorageModel,
    ProxyStorageModelWithContentObjectField,
    ProxyStorageModelWithOriginalStorageName,
    ProxyStorageModelWithContentObjectFieldAndOriginalStorageName
)
from .base_test_cases import (
    TestExistsMixin,
    TestSaveMixin,
    TestDeleteMixin,
    TestOpenMixin,
)


class SimpleFileSystemProxyStorage(ProxyStorageBase):
    pass


class PrepareMixin(object):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.file_name = u'hello.txt'
        self.content = u'some content'
        self.content_file = ContentFile(self.content)
        self.file_full_path = os.path.join(self.temp_dir, self.file_name)
        self.proxy_storage.original_storage = FileSystemStorage(location=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)


test_case_bases = [
    (TestExistsMixin, PrepareMixin, TestCase),
    (TestSaveMixin, PrepareMixin, TestCase),
    (TestDeleteMixin, PrepareMixin, TestCase),
    (TestOpenMixin, PrepareMixin, TestCase)
]

meta_backend_instances = [
    ORMMetaBackend(model=ProxyStorageModel),
    ORMMetaBackend(model=ProxyStorageModelWithContentObjectField),
    ORMMetaBackend(model=ProxyStorageModelWithOriginalStorageName),
    ORMMetaBackend(model=ProxyStorageModelWithContentObjectFieldAndOriginalStorageName),
    MongoMetaBackend(
        database=MongoClient('localhost', settings.MONGO_DATABASE_PORT)[settings.MONGO_DATABASE_NAME],
        collection=settings.MONGO_META_BACKEND_COLLECTION_NAME
    )
]


# test simple proxy storage
locals().update(
    create_test_cases_for_proxy_storage(
        SimpleFileSystemProxyStorage,
        test_case_bases,
        meta_backend_instances
    )
)