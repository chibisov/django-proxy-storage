# -*- coding: utf-8 -*-
from mock import patch, Mock

from django.test import TestCase
from django.core.files.base import ContentFile

from proxy_storage.settings import proxy_storage_settings


class MetaBackendObjectTestBaseMixin(object):
    def setUp(self):
        self.path = self.proxy_storage.save('hello.txt', ContentFile('world'))
        self.meta_backend_obj = self.proxy_storage.meta_backend.get(self.path)

    def test_get_proxy_storage(self):
        self.assertEqual(type(self.meta_backend_obj.get_proxy_storage()), type(self.proxy_storage))

    def test_get_original_storage(self):
        self.assertEqual(self.meta_backend_obj.get_original_storage(), self.proxy_storage.get_original_storage())

    def test_get_original_storage_full_path(self):
        self.assertEqual(
            self.meta_backend_obj.get_original_storage_full_path(),
            self.proxy_storage.get_original_storage_full_path(self.path)
        )

    def test_get_original_storage_full_path__should_be_called_with_meta_backend_obj_param(self):
        with patch.object(type(self.proxy_storage), 'get_original_storage_full_path', Mock()) as mock:
            self.meta_backend_obj.get_original_storage_full_path()
            mock.assert_called_once_with(path=self.meta_backend_obj['path'], meta_backend_obj=self.meta_backend_obj)


class ORMMetaBackendObjectTestBase(MetaBackendObjectTestBaseMixin, TestCase):
    proxy_storage = proxy_storage_settings.PROXY_STORAGE_CLASSES['simple_orm']()


class MongoMetaBackendObjectTestBase(MetaBackendObjectTestBaseMixin, TestCase):
    proxy_storage = proxy_storage_settings.PROXY_STORAGE_CLASSES['simple_mongo']()