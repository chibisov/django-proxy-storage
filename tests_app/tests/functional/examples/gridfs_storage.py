"""
From
https://bitbucket.org/david/django-storages/src/f153a70ba254dc129d9403546809a02256ef75b5/storages/backends/mongodb.py?at=default
"""
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import File
from django.core.files.storage import Storage
from django.db import connections
from django.utils.encoding import force_text

from gridfs import GridFS, NoFile


class GridFSStorage(Storage):
    def __init__(self, database, collection, *args, **kwargs):
        self.database = database
        self.collection = collection
        super(GridFSStorage, self).__init__(*args, **kwargs)

    @property
    def fs(self):
        return GridFS(self.database, self.collection)

    def _open(self, name, mode='rb'):
        return GridFSFile(name, self, mode=mode)

    def _save(self, name, content):
        name = force_text(name).replace('\\', '/')
        content.open()
        kwargs = {
            'filename': name,
            'encoding': 'utf-8'
        }
        if hasattr(content.file, 'content_type'):
            kwargs['content_type'] = content.file.content_type
        file = self.fs.new_file(**kwargs)
        if hasattr(content, 'chunks'):
            for chunk in content.chunks():
                file.write(chunk)
        else:
            file.write(content)
        file.close()
        content.close()
        return name

    def get_valid_name(self, name):
        return force_text(name).strip().replace('\\', '/')

    def delete(self, name):
        f = self._open(name, 'r')
        return self.fs.delete(f.file._id)

    def exists(self, name):
        try:
            self.fs.get_last_version(name)
            return True
        except NoFile:
            return False

    def listdir(self, path):
        return ((), self.fs.list())

    def size(self, name):
        try:
            return self.fs.get_last_version(name).length
        except NoFile:
            raise ValueError('File with name "%s" does not exist' % name)

    def url(self, name):
        raise NotImplementedError()


class GridFSFile(File):
    def __init__(self, name, storage, mode):
        self.name = name
        self._storage = storage
        self._mode = mode

        try:
            self.file = storage.fs.get_last_version(name)
        except NoFile:
            raise ValueError("The file doesn't exist.")

    @property
    def size(self):
        return self.file.length

    def read(self, num_bytes=None):
        if num_bytes is None:
            return self.file.read()
        else:
            return self.file.read(num_bytes)

    def write(self, content):
        raise NotImplementedError()

    def close(self):
        self.file.close()