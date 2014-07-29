# -*- coding: utf-8 -*-
from django.test import TestCase

from proxy_storage.settings import proxy_storage_settings

from tests_app.proxy_storages import SimpleORMProxyStorage, SimpleMongoProxyStorage


class TestSettings(TestCase):
    def test_proxy_storage_classes(self):
        expected = {
            'simple_orm': SimpleORMProxyStorage,
            'simple_mongo': SimpleMongoProxyStorage
        }
        self.assertEqual(proxy_storage_settings.PROXY_STORAGE_CLASSES, expected)

    def test_proxy_storage_classes_inverted(self):
        expected = {
            SimpleORMProxyStorage: 'simple_orm',
            SimpleMongoProxyStorage: 'simple_mongo',
        }
        self.assertEqual(proxy_storage_settings.PROXY_STORAGE_CLASSES_INVERTED, expected)