# -*- coding: utf-8 -*-
from django.core.files.storage import FileSystemStorage
from django.conf import settings

from proxy_storage.storages.base import ProxyStorageBase
from proxy_storage.meta_backends.orm import ORMMetaBackend
from proxy_storage.meta_backends.mongo import MongoMetaBackend

from tests_app.models import ProxyStorageModel
from pymongo import MongoClient


class SimpleORMProxyStorage(ProxyStorageBase):
    original_storage = FileSystemStorage(location=settings.TEMP_DIR)
    meta_backend = ORMMetaBackend(model=ProxyStorageModel)


class SimpleMongoProxyStorage(ProxyStorageBase):
    original_storage = FileSystemStorage(location=settings.TEMP_DIR)
    meta_backend = MongoMetaBackend(
        database=MongoClient('localhost', settings.MONGO_DATABASE_PORT)[settings.MONGO_DATABASE_NAME],
        collection=settings.MONGO_META_BACKEND_COLLECTION_NAME
    )