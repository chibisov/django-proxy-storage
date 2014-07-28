# -*- coding: utf-8 -*-
from django.test import TestCase
from django.conf import settings

from proxy_storage.meta_backends.base import MetaBackendObject
from proxy_storage.testutils import override_proxy_storage_settings

from pymongo import MongoClient


class OriginalStorageMockClass(object):
    pass


class ProxyStorageMockClass(object):
    original_storage = OriginalStorageMockClass()

    def get_original_storage(self, meta_backend_obj=None):
        return meta_backend_obj['original_storage_name']

    def get_original_storage_full_path(self, meta_backend_obj=None):
        return meta_backend_obj['full_original_storage_path']


class AnotherProxyStorageMockClass(object):
    original_storage = OriginalStorageMockClass()

    def get_original_storage(self, meta_backend_obj=None):
        return meta_backend_obj['original_storage_name']


@override_proxy_storage_settings(PROXY_STORAGE_CLASSES={
    'proxy_storage_mock': ProxyStorageMockClass,
    'another_proxy_storage_mock': AnotherProxyStorageMockClass,
})
class MetaBackendObjectTest(TestCase):
    def test_should_behave_like_dict(self):
        source_dict = {
            'hello': 'world'
        }
        meta_backend_obj = MetaBackendObject(source_dict)
        self.assertEqual(meta_backend_obj, source_dict)

    def test_get_proxy_storage(self):
        experiments = [
            {
                'proxy_storage_name': 'proxy_storage_mock',
                'proxy_storage_class': ProxyStorageMockClass,
            },
            {
                'proxy_storage_name': 'another_proxy_storage_mock',
                'proxy_storage_class': AnotherProxyStorageMockClass,
            }
        ]

        for exp in experiments:
            meta_backend_obj = MetaBackendObject({
                'proxy_storage_name': exp['proxy_storage_name']
            })
            self.assertIsInstance(meta_backend_obj.get_proxy_storage(), exp['proxy_storage_class'])

    def test_get_original_storage(self):
        experiments = [
            {
                'proxy_storage_name': 'proxy_storage_mock',
                'original_storage_name': 'some original storage name'
            },
            {
                'proxy_storage_name': 'another_proxy_storage_mock',
                'original_storage_name': 'another original storage name'
            }
        ]

        for exp in experiments:
            meta_backend_obj = MetaBackendObject({
                'proxy_storage_name': exp['proxy_storage_name'],
                'original_storage_name': exp['original_storage_name']
            })
            self.assertEqual(meta_backend_obj.get_original_storage(), exp['original_storage_name'])

    def test_get_original_storage_full_path(self):
        meta_backend_obj = MetaBackendObject({
            'proxy_storage_name': 'proxy_storage_mock',
            'original_storage_name': 'some original storage name',
            'full_original_storage_path': '/files/hello.txt'
        })
        self.assertEqual(meta_backend_obj.get_original_storage_full_path(), '/files/hello.txt')