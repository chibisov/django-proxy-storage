# -*- coding: utf-8 -*-
from django.test import TestCase

from proxy_storage.settings import proxy_storage_settings

from tests_app.proxy_storages import SimpleORMProxyStorage


class TestSettings(TestCase):
    def test_proxy_storage_classes(self):
        expected = {
            'simple_orm': SimpleORMProxyStorage,
        }
        self.assertEqual(proxy_storage_settings.PROXY_STORAGE_CLASSES, expected)

    def test_proxy_storage_classes_inverted(self):
        expected = {
            SimpleORMProxyStorage: 'simple_orm',
        }
        self.assertEqual(proxy_storage_settings.PROXY_STORAGE_CLASSES_INVERTED, expected)