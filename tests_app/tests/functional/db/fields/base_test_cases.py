# -*- coding: utf-8 -*-
import shutil
import tempfile

import django
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from .models import SurveyAnswer


class ProxyStorageFileFieldTestMixin(object):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.content = 'some content'
        self.content_file = ContentFile(self.content)
        if django.VERSION[0] == 1 and django.VERSION[1] >= 10:
            SurveyAnswer._meta.get_field('resume').storage = self.proxy_storage
        else:
            SurveyAnswer._meta.get_field_by_name('resume')[0].storage = self.proxy_storage
        self.proxy_storage.original_storage = FileSystemStorage(location=self.temp_dir)

        self.user = User.objects.create(username='web-chib')

        self.survey_answer = SurveyAnswer.objects.create(
            id=123,
            user=self.user,
        )
        self.survey_answer.resume.save('resume.txt', self.content_file)
        self.saved_path = str(self.survey_answer.resume)
        self.meta_backend_instance = self.survey_answer.resume.storage.meta_backend.get(path=self.saved_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_proxy_storage_meta_backend_instance_must_be_created(self):
        self.assertTrue(self.survey_answer.resume.storage.meta_backend.exists(path=self.saved_path))

    def test_should_assign_content_object(self):
        self.assertEqual(self.meta_backend_instance['content_type_id'], ContentType.objects.get_for_model(SurveyAnswer).id)
        self.assertEqual(self.meta_backend_instance['object_id'], self.survey_answer.id)

    def test_should_assign_field_name(self):
        self.assertEqual(self.meta_backend_instance['field'], 'resume')
