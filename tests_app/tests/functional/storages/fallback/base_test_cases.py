# -*- coding: utf-8 -*-
import tempfile
import shutil
import os
from mock import Mock

from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage

from proxy_storage.storages.fallback import OriginalStorageFallbackMixin
from tests_app.tests.functional.storages.base.multiple_original_storages_mixin.base_test_cases import (
    TestExistsMixin as TestExistsMixinBase,
    TestSaveMixin as TestSaveMixinBase,
    TestDeleteMixin as TestDeleteMixinBase,
    TestOpenMixin as TestOpenMixinBase,
)


class FileSystemFallbackStorage(OriginalStorageFallbackMixin, FileSystemStorage):
    fallback_exceptions = (IOError, OSError)


class PrepareMixin(object):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_dir_2 = tempfile.mkdtemp()
        self.file_name = u'hello.txt'
        self.content = u'some content'
        self.content_file = ContentFile(self.content)
        self.file_full_path = os.path.join(self.temp_dir, self.file_name)
        self.proxy_storage.original_storages = [
            ['original_storage_1', FileSystemFallbackStorage(location=self.temp_dir)],
            ['original_storage_2', FileSystemFallbackStorage(location=self.temp_dir_2)],
        ]
        self.proxy_storage._init_original_storages()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        shutil.rmtree(self.temp_dir_2)


class TestExistsMixin(TestExistsMixinBase):
    pass


class TestSaveMixin(TestSaveMixinBase):
    def test_unregistered_exception_should_be_raised(self):
        self.proxy_storage.original_storages[0][1]._save = Mock(side_effect=IndexError)

        try:
            self.proxy_storage.save(self.file_name, self.content_file)
        except IndexError:
            pass
        else:
            self.fail('Not registered in "fallback_exceptions" exception should be raised')

    def test_if_raised_registered_exception_then_should_fallback_to_next_original_storage(self):
        self.proxy_storage.original_storages[0][1]._save = Mock(side_effect=OSError)

        try:
            saved_path = self.proxy_storage.save(self.file_name, self.content_file)
        except OSError:
            self.fail('Registered in "fallback_exceptions" exception should be caught')
        meta_backend_obj = self.proxy_storage.meta_backend.get(path=saved_path)
        msg = 'Next original storage should be used for storing content if previous failed with registered exception'
        self.assertEqual(meta_backend_obj['original_storage_name'], 'original_storage_2', msg=msg)

    def test_latest_used_original_storage_should_become_main_original_storage(self):
        self.proxy_storage.original_storages[0][1]._save = Mock(side_effect=OSError)

        self.assertEqual(self.proxy_storage.original_storage, self.proxy_storage.original_storages[0][1])
        self.proxy_storage.save(self.file_name, self.content_file)
        # after fallback to next orginal storage
        self.assertEqual(self.proxy_storage.original_storage, self.proxy_storage.original_storages[1][1])

    def test_should_raise_latest_exception_if_no_original_storage_could_store_content(self):
        self.proxy_storage.original_storages[0][1]._save = Mock(side_effect=IOError)
        self.proxy_storage.original_storages[1][1]._save = Mock(side_effect=OSError)

        try:
            self.proxy_storage.save(self.file_name, self.content_file)
        except OSError:
            pass
        else:
            self.fail('If no one original storage could store content, then latest exception should be raise '
                      'even if it is registered for falling back')

    def test_should_raise_exception_if_original_storage_does_not_have_interfaces_to_get_fallback_exceptions(self):
        self.proxy_storage.original_storages[0][1] = FileSystemStorage()
        self.proxy_storage.original_storages[0][1]._save = Mock(side_effect=IOError)
        self.proxy_storage._init_original_storages()

        try:
            self.proxy_storage.save(self.file_name, self.content_file)
        except IOError:
            pass
        else:
            self.fail('If original storage does not have "get_fallback_exception", then storage exception should be '
                      'raised')

    def test_forced_original_storage_should_raise_first_exception(self):
        self.proxy_storage.original_storages[0][1]._save = Mock(side_effect=IOError)

        try:
            self.proxy_storage.save(self.file_name, self.content_file, using='original_storage_1')
        except IOError:
            pass
        else:
            self.fail('Forced original storage should raise first exception even if it is registered and there are '
                      'storages for fallback')


class TestDeleteMixin(TestDeleteMixinBase):
    pass


class TestOpenMixin(TestOpenMixinBase):
    pass