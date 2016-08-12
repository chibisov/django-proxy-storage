# -*- coding: utf-8 -*-
import re

from django.test import TestCase
from django.db import IntegrityError
from django.contrib.contenttypes.models import ContentType

from proxy_storage.meta_backends.base import MetaBackendObject, MetaBackendObjectDoesNotExist
from proxy_storage.meta_backends.orm import ORMMetaBackend
from proxy_storage.testutils import override_proxy_storage_settings

from .models import (
    UnitMetaBackendsOrmProxyStorageModel as ProxyStorageModel,
    UnitMetaBackendsOrmSimpleProxyStorageModel as SimpleProxyStorageModel,
    UnitMetaBackendsOrmBook as Book,
    UnitMetaBackendsOrmProxyStorageWithContentObjectFieldModel as ProxyStorageWithContentObjectFieldModel,
    UnitMetaBackendsOrmProxyStorageWithOriginalStorageNameModel as ProxyStorageWithOriginalStorageNameModel,
)


class ORMMetaBackendTest(TestCase):
    def setUp(self):
        self.orm_meta_backend_instance = ORMMetaBackend(model=ProxyStorageModel)

    def test_create__should_create_model_instance_with_data(self):
        data = {
            'path': '/hello/world.txt',
            'some_attr': 'some attr value',
            'another_attr': 'another attr value',
        }
        self.orm_meta_backend_instance.create(data=data)
        self.assertEqual(self.orm_meta_backend_instance.model.objects.count(), 1)
        obj = self.orm_meta_backend_instance.model.objects.all()[0]
        self.assertEqual(obj.path, data['path'])
        self.assertEqual(obj.some_attr, data['some_attr'])
        self.assertEqual(obj.another_attr, data['another_attr'])

    def test_create__should_return_meta_backend_object(self):
        data = {
            'path': '/hello/world.txt',
            'some_attr': 'some attr value',
            'another_attr': 'another attr value',
        }
        meta_backend_object = self.orm_meta_backend_instance.create(data=data)
        self.assertIsInstance(meta_backend_object, MetaBackendObject)
        model_obj = self.orm_meta_backend_instance.model.objects.all()[0]
        self.assertEqual(model_obj.id, meta_backend_object.get('id'))
        self.assertEqual(model_obj.path, meta_backend_object.get('path'))
        self.assertEqual(model_obj.some_attr, meta_backend_object.get('some_attr'))
        self.assertEqual(model_obj.another_attr, meta_backend_object.get('another_attr'))

    def test_get__should_return_meta_backend_object(self):
        data = {
            'path': '/hello/world.txt',
            'some_attr': 'some attr value',
            'another_attr': 'another attr value',
        }
        self.orm_meta_backend_instance.create(data=data)
        meta_backend_object = self.orm_meta_backend_instance.get(path=data.get('path'))
        self.assertIsInstance(meta_backend_object, MetaBackendObject)
        model_obj = self.orm_meta_backend_instance.model.objects.all()[0]
        self.assertEqual(model_obj.id, meta_backend_object.get('id'))
        self.assertEqual(model_obj.path, meta_backend_object.get('path'))
        self.assertEqual(model_obj.some_attr, meta_backend_object.get('some_attr'))
        self.assertEqual(model_obj.another_attr, meta_backend_object.get('another_attr'))

    def test_get__should_raise_special_exception_if_object_does_not_exist(self):
        expected_message = '{0} matching query does not exist.'.format(
            self.orm_meta_backend_instance.model.__name__
        )
        caught_right_exception = False
        try:
            self.orm_meta_backend_instance.get(path='/some/not/existing/path')
        except MetaBackendObjectDoesNotExist as exc:
            message = str(exc)
            self.assertEqual(expected_message, message)
            caught_right_exception = True
        except Exception:
            pass
        msg = 'Meta backend\'s "get" method should raise MetaBackendObjectDoesNotExist if could not find object'
        self.assertTrue(caught_right_exception, msg)

    def test_update_should_update_data(self):
        data = {
            'path': '/hello/world.txt',
            'some_attr': 'some attr value',
            'another_attr': 'another attr value',
        }
        self.orm_meta_backend_instance.create(data=data)
        update_data = {
            'some_attr': 'some attr value updated',
            'another_attr': 'another attr value updated',
        }
        self.orm_meta_backend_instance.update(path=data['path'], update_data=update_data)
        meta_backend_object = self.orm_meta_backend_instance.get(path=data['path'])
        self.assertEqual(meta_backend_object['some_attr'], update_data['some_attr'])
        self.assertEqual(meta_backend_object['another_attr'], update_data['another_attr'])

    def test_delete__should_delete_model_instance_with_exact_path(self):
        self.orm_meta_backend_instance.model.objects.create(path='/file/one')
        self.orm_meta_backend_instance.model.objects.create(path='/file/two')
        self.assertEqual(self.orm_meta_backend_instance.model.objects.count(), 2)
        self.orm_meta_backend_instance.delete(path='/file/one')
        self.assertEqual(self.orm_meta_backend_instance.model.objects.count(), 1)
        obj = self.orm_meta_backend_instance.model.objects.all()[0]
        self.assertEqual(obj.path, '/file/two')

    def test_exists__should_return_true__if_object_with_exact_path_exists(self):
        path = '/file/one'
        self.orm_meta_backend_instance.model.objects.create(path=path)
        self.assertTrue(self.orm_meta_backend_instance.exists(path))

    def test_exists__should_return_false__if_object_with_exact_path_does_not_exist(self):
        path = '/file/one'
        self.orm_meta_backend_instance.model.objects.create(path=path)
        self.assertFalse(self.orm_meta_backend_instance.exists('/file/two'))


class OriginalStorageMockClass(object):
    pass


class ProxyStorageMockClass(object):
    original_storage = OriginalStorageMockClass()

    def get_original_storage(self, meta_backend_obj=None):
        return self.original_storage


class AnotherProxyStorageMockClass(object):
    original_storage = OriginalStorageMockClass()

    def get_original_storage(self, meta_backend_obj=None):
        return self.original_storage


@override_proxy_storage_settings(PROXY_STORAGE_CLASSES={
    'proxy_storage_mock': ProxyStorageMockClass,
    'another_proxy_storage_mock': AnotherProxyStorageMockClass,
})
class ProxyStorageModelBaseTest(TestCase):
    def setUp(self):
        self.model = SimpleProxyStorageModel

    def test_should_raise_error_if_path_is_not_unique(self):
        path = '/path/file.txt'
        self.model.objects.create(
            path=path,
            proxy_storage_name='another_proxy_storage_mock'
        )
        try:
            self.model.objects.create(
                path=path,
                proxy_storage_name='another_proxy_storage_mock'
            )
        except IntegrityError as e:
            error_msg = str(e)
        else:
            error_msg = None
        self.assertTrue(re.search(r'unique', error_msg, flags=re.IGNORECASE))

    def test_unicode(self):
        instance = self.model.objects.create(
            path='/path/file.txt',
            proxy_storage_name='another_proxy_storage_mock',
            original_storage_path='/original/file.txt',
        )
        expected_name = u'AnotherProxyStorageMockClass /path/file.txt => OriginalStorageMockClass /original/file.txt'
        self.assertEqual(instance.__unicode__(), expected_name)


class ContentObjectFieldMixinTest(TestCase):
    def setUp(self):
        self.model = ProxyStorageWithContentObjectFieldModel

    def test_should_add_content_object_and_field_fields(self):
        book = Book.objects.create(title='REST with Django')
        content_type = ContentType.objects.get_for_model(Book)

        model_instance = self.model.objects.create(
            path='/some/file.txt',
            proxy_storage_name='some_proxy_storage_name',
            original_storage_path='/original/path.txt',
            content_type_id=content_type.id,
            object_id=book.id,
            field='title'
        )
        self.assertEqual(model_instance.content_type_id, content_type.id)
        self.assertEqual(model_instance.field, 'title')

    def test_should_allow_creation_of_instance_without_generic_content_and_field_data(self):
        self.model.objects.create(
            path='/some/file.txt',
            proxy_storage_name='some_proxy_storage_name',
            original_storage_path='/original/path.txt',
        )


class OriginalStorageNameMixinTest(TestCase):
    def setUp(self):
        self.model = ProxyStorageWithOriginalStorageNameModel

    def test_should_add_original_storage_name_field(self):
        model_instance = self.model.objects.create(
            path='/some/file.txt',
            proxy_storage_name='some_proxy_storage_name',
            original_storage_path='/original/path.txt',
            original_storage_name='some_original_storage_name'
        )
        self.assertEqual(model_instance.original_storage_name, 'some_original_storage_name')

    def test_should_allow_creation_of_instance_without_original_storage_name(self):
        self.model.objects.create(
            path='/some/file.txt',
            proxy_storage_name='some_proxy_storage_name',
            original_storage_path='/original/path.txt',
        )
