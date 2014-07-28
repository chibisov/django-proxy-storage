# -*- coding: utf-8 -*-
from pymongo import MongoClient

from django.test import TestCase
from django.conf import settings

from proxy_storage.meta_backends.orm import ORMMetaBackend
from proxy_storage.meta_backends.mongo import MongoMetaBackend
from proxy_storage.storages.base import ProxyStorageBase
from proxy_storage.storages.fallback import FallbackProxyStorageMixin
from proxy_storage.testutils import create_test_cases_for_proxy_storage

from tests_app.models import (
    ProxyStorageModelWithOriginalStorageName,
    ProxyStorageModelWithContentObjectFieldAndOriginalStorageName
)
from .base_test_cases import (
    PrepareMixin,
    TestExistsMixin,
    TestSaveMixin,
    TestDeleteMixin,
    TestOpenMixin,
)


class FileSystemProxyStorageWithFallback(FallbackProxyStorageMixin, ProxyStorageBase):
    pass


base_test_case_classes = [
    (TestExistsMixin, PrepareMixin, TestCase),
    (TestSaveMixin, PrepareMixin, TestCase),
    (TestDeleteMixin, PrepareMixin, TestCase),
    (TestOpenMixin, PrepareMixin, TestCase)
]

meta_backend_instances = [
    ORMMetaBackend(model=ProxyStorageModelWithOriginalStorageName),
    ORMMetaBackend(model=ProxyStorageModelWithContentObjectFieldAndOriginalStorageName),
    MongoMetaBackend(
        database=MongoClient('localhost', settings.MONGO_DATABASE_PORT)[settings.MONGO_DATABASE_NAME],
        collection=settings.MONGO_META_BACKEND_COLLECTION_NAME
    )
]


# test default behaviour of proxy storage with fallback
locals().update(
    create_test_cases_for_proxy_storage(
        FileSystemProxyStorageWithFallback,
        base_test_case_classes,
        meta_backend_instances
    )
)