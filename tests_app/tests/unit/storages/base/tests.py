# -*- coding: utf-8 -*-
from mock import patch, Mock

from django.test import TestCase

from proxy_storage.storages.base import ProxyStorageBase


class ProxyStorage(ProxyStorageBase):
    original_storage = Mock()


class ProxyStorageBaseTest___get_original_storage_full_path(TestCase):
    def setUp(self):
        self.proxy_storage = ProxyStorage()

    def test_with_original_storage_with_implemented_path(self):
        def path(name):
            return '/files/' + name

        with patch.object(self.proxy_storage.original_storage, 'path', path):
            response = self.proxy_storage.get_original_storage_full_path('some/path/')
            self.assertEqual(response, '/files/' + 'some/path/')

    def test_with_original_storage_with_not_implemented_path(self):
        with patch.object(self.proxy_storage.original_storage, 'path', Mock(side_effect=NotImplementedError)):
            response = self.proxy_storage.get_original_storage_full_path('some/path/')
            self.assertEqual(response, 'some/path/')