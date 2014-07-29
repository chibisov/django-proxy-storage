# -*- coding: utf-8 -*-
import tempfile
import shutil
import os
from mock import Mock

from django.core.files.base import ContentFile
from django.utils.encoding import force_text
from django.core.files.storage import FileSystemStorage
from django.conf import settings

from .models import JobApply


class PrepareMixin(object):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.file_name = u'hello.txt'
        self.content = u'some content'
        self.content_file = ContentFile(self.content)
        self.file_full_path = os.path.join(self.temp_dir, self.file_name)
        self.proxy_storage.original_storage = FileSystemStorage(location=self.temp_dir)
        JobApply._meta.get_field_by_name('resume')[0].storage = self.proxy_storage.original_storage

    def tearDown(self):
        shutil.rmtree(self.temp_dir)


class TestMigrationToProxyStorageMixin(PrepareMixin):
    def test_should_create_meta_backend_objects(self):
        job_apply = JobApply.objects.create()
        job_apply.resume.save('hello.txt', ContentFile('world'))
        old_file_name = str(job_apply.resume)
        new_file_name = self.proxy_storage.save(
            name=old_file_name,
            content=job_apply.resume,
            original_storage_path=old_file_name
        )
        JobApply.objects.filter(id=job_apply.id).update(resume=new_file_name)

        # change storage to proxy-storage
        JobApply._meta.get_field_by_name('resume')[0].storage = self.proxy_storage

        fresh_job_apply = JobApply.objects.get(pk=job_apply.id)
        self.assertEqual(str(fresh_job_apply.resume), new_file_name)
        self.assertEqual(force_text(fresh_job_apply.resume.read()), 'world')

        # test meta backend object
        meta_backend_object = self.proxy_storage.meta_backend.get(new_file_name)
        self.assertEqual(meta_backend_object['original_storage_path'], old_file_name)
        self.assertEqual(meta_backend_object['path'], new_file_name)