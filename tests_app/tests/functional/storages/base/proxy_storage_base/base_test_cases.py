# -*- coding: utf-8 -*-
from django.core.files.base import ContentFile
from django.utils.encoding import force_text

from proxy_storage.settings import proxy_storage_settings


class TestExistsMixin(object):
    def test_file_should_not_exists_by_default(self):
        self.assertFalse(self.proxy_storage.exists(self.file_full_path))

    def test_exists(self):
        self.assertFalse(self.proxy_storage.exists(self.file_full_path))
        self.proxy_storage.meta_backend.create(
            data={
                'path': self.file_full_path + 'bad_path',
                'original_storage_path': self.file_name
            }
        )
        self.assertFalse(self.proxy_storage.exists(self.file_full_path))
        self.proxy_storage.meta_backend.create(
            data={
                'path': self.file_full_path,
                'original_storage_path': self.file_name
            }
        )
        self.assertTrue(self.proxy_storage.exists(self.file_full_path))


class TestSaveMixin(object):
    def test_save(self):
        saved_file_name = self.proxy_storage.save(self.file_name, self.content_file)

        msg = 'should use full origin storage file path for "path" attribute'
        self.assertEqual(saved_file_name, self.file_full_path, msg)

        msg = 'exists should return True if file saved'
        self.assertTrue(self.proxy_storage.exists(saved_file_name), msg)

        msg = 'should save file content to original storage'
        self.assertTrue(self.proxy_storage.original_storage.exists(self.file_name), msg)
        self.assertEqual(
            self.proxy_storage.original_storage.open(self.file_name, 'r').read(),
            self.content,
            msg
        )

        meta_backend_obj = self.proxy_storage.meta_backend.get(path=saved_file_name)

        self.assertEqual(meta_backend_obj['path'], saved_file_name)
        self.assertEqual(meta_backend_obj['original_storage_path'], self.file_name)
        self.assertEqual(
            meta_backend_obj['proxy_storage_name'],
            proxy_storage_settings.PROXY_STORAGE_CLASSES_INVERTED[type(self.proxy_storage)]
        )

    def test_save_with_original_storage_file_already_exists(self):
        second_content = 'some second content'
        second_content_file = ContentFile(second_content)

        saved_file_name = self.proxy_storage.save(self.file_name, self.content_file)
        second_saved_file_name = self.proxy_storage.save(self.file_name, second_content_file)

        self.assertNotEqual(saved_file_name, second_saved_file_name)
        self.assertEqual(second_saved_file_name.split('/')[-1], 'hello_1.txt')

        model_instance = self.proxy_storage.meta_backend.get(path=saved_file_name)
        second_model_instance = self.proxy_storage.meta_backend.get(path=second_saved_file_name)

        self.assertEqual(
            self.proxy_storage.original_storage.open(model_instance['original_storage_path'], 'r').read(),
            self.content
        )
        self.assertEqual(
            self.proxy_storage.original_storage.open(second_model_instance['original_storage_path'], 'r').read(),
            second_content
        )

    def test_save_with_proxy_storage_path_already_exists(self):
        self.proxy_storage.meta_backend.create(
            data={
                'path': self.file_full_path,
                'original_storage_path': self.file_name
            }
        )

        saved_file_name = self.proxy_storage.save(self.file_name, self.content_file)
        msg = 'should take next available name for proxy storage path'
        self.assertNotEqual(saved_file_name, self.file_full_path, msg)

    def test_with_original_storage_path_argument_should_not_perform_saving_to_original_storage(self):
        original_storage_path = 'hello.txt'
        saved_file_name = self.proxy_storage.save(
            self.file_name,
            self.content_file,
            original_storage_path=original_storage_path
        )
        meta_backend_obj = self.proxy_storage.meta_backend.get(path=saved_file_name)

        self.assertTrue(self.proxy_storage.exists(saved_file_name))
        self.assertFalse(self.proxy_storage.original_storage.exists(saved_file_name))
        self.assertEqual(meta_backend_obj['original_storage_path'], original_storage_path)


class TestDeleteMixin(object):
    def test_delete_existing_file(self):
        saved_file_name = self.proxy_storage.save(self.file_name, self.content_file)
        self.proxy_storage.delete(saved_file_name)

        self.assertFalse(self.proxy_storage.exists(saved_file_name))
        self.assertFalse(self.proxy_storage.original_storage.exists(self.file_name))

    def test_delete_not_existing_in_proxy_storage_file(self):
        try:
            self.proxy_storage.delete('file.txt')
        except IOError as e:
            self.assertEqual(str(e), 'File not found: file.txt')
        else:
            self.fail('Should raise IOError if file not exists')


class TestOpenMixin(object):
    def test_simple_open(self):
        saved_file_name = self.proxy_storage.save(self.file_name, self.content_file)
        opened = self.proxy_storage.open(saved_file_name)
        self.assertEqual(force_text(opened.read()), self.content)

    def test_proxy_storage_path_and_original_storage_path_has_different_destinations(self):
        saved_file_name = self.proxy_storage.save(self.file_name, self.content_file)
        new_path = 'proxy/path'
        self.proxy_storage.meta_backend.update(path=saved_file_name, update_data={'path': new_path})
        try:
            opened = self.proxy_storage.open(new_path)
        except IOError:
            self.fail('Original storage file path should be taken from meta_backend object')
        self.assertEqual(force_text(opened.read()), self.content)

    def test_proxy_storage_path_does_not_exist(self):
        try:
            self.proxy_storage.open('/not/existing/proxy/path')
        except IOError as e:
            error_message = str(e)
            expected = u'No such {0} object with path: /not/existing/proxy/path'.format(
                type(self.proxy_storage.meta_backend).__name__
            )
            self.assertEqual(error_message, expected)
        else:
            self.fail('If trying to open path that not exists in proxy storage model, then should raise IOError')