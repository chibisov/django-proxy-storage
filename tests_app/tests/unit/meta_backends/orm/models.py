# -*- coding: utf-8 -*-
from django.db import models

from proxy_storage.meta_backends.orm import (
    ProxyStorageModelBase,
    ContentObjectFieldMixin,
    OriginalStorageNameMixin
)


class UnitMetaBackendsOrmProxyStorageModel(models.Model):
    path = models.CharField(max_length=10)
    some_attr = models.CharField(max_length=10, null=True)
    another_attr = models.CharField(max_length=10, null=True)

    class Meta:
        app_label = 'tests_app'
        verbose_name = 'proxy storage model'


class UnitMetaBackendsOrmSimpleProxyStorageModel(ProxyStorageModelBase):

    class Meta:
        app_label = 'tests_app'
        verbose_name = 'simple proxy storage model'


class UnitMetaBackendsOrmBook(models.Model):
    title = models.CharField(max_length=100)

    class Meta:
        app_label = 'tests_app'


class UnitMetaBackendsOrmProxyStorageWithContentObjectFieldModel(ContentObjectFieldMixin, ProxyStorageModelBase):

    class Meta:
        app_label = 'tests_app'
        verbose_name = 'Proxy storage with field'


class UnitMetaBackendsOrmProxyStorageWithOriginalStorageNameModel(OriginalStorageNameMixin, ProxyStorageModelBase):

    class Meta:
        app_label = 'tests_app'
        verbose_name = 'proxy storage with orig'