# -*- coding: utf-8 -*-
from django.core.files.storage import FileSystemStorage
from proxy_storage.storages.base import ProxyStorageBase
from proxy_storage.meta_backends.orm import ORMMetaBackend

from tests_app.models import ProxyStorageModel


class SimpleORMProxyStorage(ProxyStorageBase):
    original_storage = FileSystemStorage()
    meta_backend = ORMMetaBackend(model=ProxyStorageModel)