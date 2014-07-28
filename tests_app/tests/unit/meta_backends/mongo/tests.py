# -*- coding: utf-8 -*-
from django.test import TestCase
from django.conf import settings

from proxy_storage.meta_backends.base import MetaBackendObject, MetaBackendObjectDoesNotExist
from proxy_storage.meta_backends.mongo import MongoMetaBackend
from proxy_storage.testutils import override_proxy_storage_settings

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError


class ORMMetaBackendTest(TestCase):
    def setUp(self):
        self.orm_meta_backend_instance = MongoMetaBackend(
            database=MongoClient('localhost', settings.MONGO_DATABASE_PORT)[settings.MONGO_DATABASE_NAME],
            collection=settings.MONGO_META_BACKEND_COLLECTION_NAME
        )

    def test_create__should_create_document_instance_with_data(self):
        data = {
            'path': '/hello/world.txt',
            'some_attr': 'some attr value',
            'another_attr': 'another attr value',
        }
        self.orm_meta_backend_instance.create(data=data)
        self.assertEqual(self.orm_meta_backend_instance.get_collection().find().count(), 1)
        obj = self.orm_meta_backend_instance.get_collection().find_one()
        self.assertEqual(obj['path'], data['path'])
        self.assertEqual(obj['some_attr'], data['some_attr'])
        self.assertEqual(obj['another_attr'], data['another_attr'])

    def test_create__should_return_meta_backend_object(self):
        data = {
            'path': '/hello/world.txt',
            'some_attr': 'some attr value',
            'another_attr': 'another attr value',
        }
        meta_backend_object = self.orm_meta_backend_instance.create(data=data)
        self.assertIsInstance(meta_backend_object, MetaBackendObject)
        mongo_obj = self.orm_meta_backend_instance.get_collection().find_one()
        self.assertEqual(mongo_obj['_id'], meta_backend_object.get('_id'))
        self.assertEqual(mongo_obj['path'], meta_backend_object.get('path'))
        self.assertEqual(mongo_obj['some_attr'], meta_backend_object.get('some_attr'))
        self.assertEqual(mongo_obj['another_attr'], meta_backend_object.get('another_attr'))

    def test_get__should_return_meta_backend_object(self):
        data = {
            'path': '/hello/world.txt',
            'some_attr': 'some attr value',
            'another_attr': 'another attr value',
        }
        self.orm_meta_backend_instance.create(data=data)
        meta_backend_object = self.orm_meta_backend_instance.get(path=data.get('path'))
        self.assertIsInstance(meta_backend_object, MetaBackendObject)
        mongo_obj = self.orm_meta_backend_instance.get_collection().find_one()
        self.assertEqual(mongo_obj['_id'], meta_backend_object.get('_id'))
        self.assertEqual(mongo_obj['path'], meta_backend_object.get('path'))
        self.assertEqual(mongo_obj['some_attr'], meta_backend_object.get('some_attr'))
        self.assertEqual(mongo_obj['another_attr'], meta_backend_object.get('another_attr'))

    def test_get__should_raise_special_exception_if_object_does_not_exist(self):
        expected_message = 'Could not find document in "{}"'.format(
            self.orm_meta_backend_instance.collection
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

    def test_delete__should_delete_document_with_exact_path(self):
        self.orm_meta_backend_instance.get_collection().insert({'path': '/file/one'})
        self.orm_meta_backend_instance.get_collection().insert({'path': '/file/two'})
        self.assertEqual(self.orm_meta_backend_instance.get_collection().find().count(), 2)
        self.orm_meta_backend_instance.delete(path='/file/one')
        self.assertEqual(self.orm_meta_backend_instance.get_collection().find().count(), 1)
        obj = self.orm_meta_backend_instance.get_collection().find_one()
        self.assertEqual(obj['path'], '/file/two')

    def test_exists__should_return_true__if_object_with_exact_path_exists(self):
        path = '/file/one'
        self.orm_meta_backend_instance.get_collection().insert({'path': path})
        self.assertTrue(self.orm_meta_backend_instance.exists(path))

    def test_exists__should_return_false__if_object_with_exact_path_does_not_exist(self):
        path = '/file/one'
        self.orm_meta_backend_instance.get_collection().insert({'path': path})
        self.assertFalse(self.orm_meta_backend_instance.exists('/file/two'))

    def test_should_raise_error_if_path_is_not_unique(self):
        path = '/file/one'
        self.orm_meta_backend_instance.create({'path': path})
        try:
            self.orm_meta_backend_instance.create({'path': path})
        except DuplicateKeyError:
            pass
        else:
            self.fail('Should raise exception when trying to create document with not unique path')

    def test_allow_database_attribute_to_be_callable(self):
        database = MongoClient('localhost', settings.MONGO_DATABASE_PORT)[settings.MONGO_DATABASE_NAME]
        orm_meta_backend_instance = MongoMetaBackend(
            database=lambda: database,
            collection=settings.MONGO_META_BACKEND_COLLECTION_NAME
        )
        try:
            collection = orm_meta_backend_instance.get_collection()
        except AttributeError:
            self.fail('"database" attribute of MongoMetaBackend should be allowed to be callable')
        self.assertEqual(collection.database, database)
        self.assertEqual(collection.name, settings.MONGO_META_BACKEND_COLLECTION_NAME)