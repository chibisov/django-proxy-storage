# -*- coding: utf-8 -*-
from django.core.files.storage import FileSystemStorage
from proxy_storage.storages.base import ProxyStorageBase
from proxy_storage.meta_backends.orm import ORMMetaBackend
from proxy_storage.meta_backends.mongo import MongoMetaBackend

from tests_app.models import ProxyStorageModel


class SimpleORMProxyStorage(ProxyStorageBase):
    original_storage = FileSystemStorage()
    meta_backend = ORMMetaBackend(model=ProxyStorageModel)


class SimpleMongoProxyStorage(ProxyStorageBase):
    original_storage = FileSystemStorage()
    meta_backend = MongoMetaBackend(database=lambda: 'nodb', collection='nocollection')