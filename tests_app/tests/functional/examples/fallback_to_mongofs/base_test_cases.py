# -*- coding: utf-8 -*-
import tempfile
import shutil
import os
from mock import Mock

from django.core.files.base import ContentFile
from django.utils.encoding import force_text
from django.core.files.storage import FileSystemStorage
from django.conf import settings

from proxy_storage.storages.fallback import OriginalStorageFallbackMixin
from pymongo import MongoClient

from tests_app.tests.functional.examples.gridfs_storage import GridFSStorage


class FileSystemFallbackStorage(OriginalStorageFallbackMixin, FileSystemStorage):
    fallback_exceptions = (IOError, OSError)


class GridFSFallbackStorage(OriginalStorageFallbackMixin, GridFSStorage):
    pass


class PrepareMixin(object):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.file_name = u'hello.txt'
        self.content = u'some content'
        self.content_file = ContentFile(self.content)
        self.file_full_path = os.path.join(self.temp_dir, self.file_name)
        self.proxy_storage.original_storages = [
            (
                'file_system',
                FileSystemFallbackStorage(location=self.temp_dir)
            ),
            (
                'mongofs',
                GridFSFallbackStorage(
                    database=MongoClient('localhost', settings.MONGO_DATABASE_PORT)[settings.MONGO_DATABASE_NAME],
                    collection=settings.MONGO_GRIDFS_COLLECTION_NAME
                )
            ),
        ]
        self.proxy_storage._init_original_storages()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)


class TestFallbackToMongoFSMixin(PrepareMixin):
    def test_should_save_to_file_system_first(self):
        saved_path = self.proxy_storage.save(self.file_name, self.content_file)

        # check in meta backends
        self.assertTrue(self.proxy_storage.meta_backend.exists(saved_path))
        meta_backend_obj = self.proxy_storage.meta_backend.get(saved_path)
        self.assertEqual(meta_backend_obj['original_storage_name'], 'file_system')
        self.assertEqual(force_text(self.proxy_storage.open(saved_path).read()), self.content)

        # check in original storages
        self.assertTrue(
            self.proxy_storage.original_storages_dict['file_system'].exists(meta_backend_obj['original_storage_path'])
        )
        self.assertFalse(
            self.proxy_storage.original_storages_dict['mongofs'].exists(meta_backend_obj['original_storage_path'])
        )

    def test_should_save_to_mongofs_if_file_system_raised_registered_exception(self):
        self.proxy_storage.original_storages_dict['file_system']._save = Mock(side_effect=IOError)

        saved_path = self.proxy_storage.save(self.file_name, self.content_file)

        # check in meta backends
        self.assertTrue(self.proxy_storage.meta_backend.exists(saved_path))
        meta_backend_obj = self.proxy_storage.meta_backend.get(saved_path)
        self.assertEqual(meta_backend_obj['original_storage_name'], 'mongofs')
        self.assertEqual(force_text(self.proxy_storage.open(saved_path).read()), self.content)

        # check in original storages
        self.assertTrue(
            self.proxy_storage.original_storages_dict['mongofs'].exists(meta_backend_obj['original_storage_path'])
        )
        self.assertFalse(
            self.proxy_storage.original_storages_dict['file_system'].exists(meta_backend_obj['original_storage_path'])
        )