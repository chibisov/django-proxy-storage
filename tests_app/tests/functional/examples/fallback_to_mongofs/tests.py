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
)
from .base_test_cases import (
    TestFallbackToMongoFSMixin,
)


class FileSystemProxyStorageWithFallbackToMongoFS(FallbackProxyStorageMixin, ProxyStorageBase):
    pass


test_case_bases = [
    (TestFallbackToMongoFSMixin, TestCase),
]

meta_backend_instances = [
    ORMMetaBackend(model=ProxyStorageModelWithOriginalStorageName),
    MongoMetaBackend(
        database=MongoClient('localhost', settings.MONGO_DATABASE_PORT)[settings.MONGO_DATABASE_NAME],
        collection=settings.MONGO_META_BACKEND_COLLECTION_NAME
    )
]


# test simple proxy storage
locals().update(
    create_test_cases_for_proxy_storage(
        FileSystemProxyStorageWithFallbackToMongoFS,
        test_case_bases,
        meta_backend_instances
    )
)