# -*- coding: utf-8 -*-
import tempfile
import shutil
import os
from mock import Mock

from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.utils.encoding import force_text

from proxy_storage.storages.fallback import OriginalStorageFallbackMixin
from tests_app.tests.functional.storages.base.proxy_storage_base.base_test_cases import (
    TestExistsMixin as TestExistsMixinBase,
    TestSaveMixin as TestSaveMixinBase,
    TestDeleteMixin as TestDeleteMixinBase,
    TestOpenMixin as TestOpenMixinBase,
)


class PrepareMixin(object):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_dir_2 = tempfile.mkdtemp()
        self.file_name = u'hello.txt'
        self.content = u'some content'
        self.content_file = ContentFile(self.content)
        self.file_full_path = os.path.join(self.temp_dir, self.file_name)
        self.proxy_storage.original_storages = [
            ('original_storage_1', FileSystemStorage(location=self.temp_dir)),
            ('original_storage_2', FileSystemStorage(location=self.temp_dir_2)),
        ]
        self.proxy_storage._init_original_storages()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        shutil.rmtree(self.temp_dir_2)


class TestExistsMixin(TestExistsMixinBase):
    pass


class TestSaveMixin(TestSaveMixinBase):
    def test_save_should_use_first_original_storage_as_default(self):
        saved_path = self.proxy_storage.save(self.file_name, self.content_file)
        meta_backend_obj = self.proxy_storage.meta_backend.get(path=saved_path)
        self.assertEqual(meta_backend_obj['original_storage_name'], 'original_storage_1')

    def test_using_attribute_should_force_usage_of_exact_original_storage(self):
        saved_path = self.proxy_storage.save(self.file_name, self.content_file, using='original_storage_2')
        meta_backend_obj = self.proxy_storage.meta_backend.get(path=saved_path)
        self.assertEqual(meta_backend_obj['original_storage_name'], 'original_storage_2')


class TestDeleteMixin(TestDeleteMixinBase):
    def test_should_delete_file_from_proper_original_storage(self):
        path = self.proxy_storage.save(self.file_name, self.content_file)
        self.proxy_storage.original_storages_dict['original_storage_2'].save(self.file_name, self.content_file)
        self.proxy_storage.original_storage = self.proxy_storage.original_storages_dict['original_storage_2']

        self.proxy_storage.delete(path)

        self.assertFalse(self.proxy_storage.original_storages_dict['original_storage_1'].exists(self.file_name))
        self.assertTrue(self.proxy_storage.original_storages_dict['original_storage_2'].exists(self.file_name))


class TestOpenMixin(TestOpenMixinBase):
    def test_should_open_file_from_proper_original_storage(self):
        path = self.proxy_storage.save(self.file_name, self.content_file)
        self.proxy_storage.original_storages_dict['original_storage_2'].save(self.file_name, ContentFile('nooooooo'))
        self.proxy_storage.original_storage = self.proxy_storage.original_storages_dict['original_storage_2']

        content = force_text(self.proxy_storage.open(path).read())

        self.assertEqual(content, self.content)