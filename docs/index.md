### Django-proxy-storage

Django-proxy-storage provides simple Django storage that proxies every operation to original storage and saves meta information about files to database.

There are no limitations for original storages. It could be default [FileSystemStorage](https://docs.djangoproject.com/en/dev/ref/files/storage/#the-filesystemstorage-class),
[S3BotoStorage](http://django-storages.readthedocs.org/en/latest/backends/amazon-S3.html) from [django-storages](http://django-storages.readthedocs.org/en/latest/index.html) or
any other storage of your choice.

Source repository is available at [https://github.com/chibisov/django-proxy-storage](https://github.com/chibisov/django-proxy-storage).

There is the [slides](https://speakerdeck.com/moscowdjango/rabota-s-failami-s-pomoshch-iu-django-proxy-storage) (in english) and comming soon video (in russian) from latest talk about django-proxy-storage at [Moscow Django](http://moscowdjango.ru/meetup/23/django-proxy-storage/).

#### Quick start

Here is default [FileSystemStorage](https://docs.djangoproject.com/en/dev/ref/files/storage/#django.core.files.storage.FileSystemStorage)
example:

    >>> from django.core.files.storage import FileSystemStorage
    >>> from django.core.files.base import ContentFile

    >>> storage = FileSystemStorage(location='/tmp/')
    >>> storage.save('hello.txt', ContentFile('world'))
    '/tmp/hello.txt'

Let's implement proxy-storage and save meta information to MongoDB database:

    # yourapp/storages.py
    from django.core.files.storage import FileSystemStorage
    from proxy_storage.storages.base import ProxyStorageBase
    from proxy_storage.meta_backends.mongo import MongoMetaBackend
    from yourapp import get_mongo_db

    class FileSystemProxyStorage(ProxyStorageBase):
        original_storage = FileSystemStorage(location='/tmp/')
        meta_backend = MongoMetaBackend(
            database=get_mongo_db(),
            collection='meta_backend_collection'
        )

Every `ProxyStorageBase` subclass must be registered in settings:

    # settings.py
    PROXY_STORAGE = {
        'PROXY_STORAGE_CLASSES': {
            'file_system_proxy_storage':
                'yourapp.storages.FileSystemProxyStorage',
        }
    }

Let's try it:

    >>> from yourapp.storages import FileSystemProxyStorage
    >>> storage = FileSystemProxyStorage()
    >>> storage.save('hello.txt', ContentFile('world'))
    '/tmp/hello.txt'

As you can see proxy-storage behaves as `FileSystemStorage`. It saves files to disk:

    $ cat /tmp/hello.txt
    world

But additionally it saved data about files to meta backend
(in current example it's mongodb):

    >>> storage = FileSystemProxyStorage()
    >>> storage.meta_backend.get('/tmp/hello.txt')
    {
        '_id': ObjectId('53d37e2856c02c1657b8ef92'),
        'proxy_storage_name': 'file_system_proxy_storage',
        'path': '/tmp/hello.txt',
        'original_storage_path': 'hello.txt'
    }

#### Use cases

Django-proxy-storage is made with easy configurability in mind, but let's emphasise most important reasons why
it exists.

**Single endpoint**

With django-proxy-storage it's easy to have access to information about files from different storages if same
[meta-backend](#meta-backend) is used.

**Authorization**

With single endpoint it's easy to implement authorization for files from different storages.
With the help of [content object field context](#content-object-field-context) it's even easier to
facilitate authorization for exact model instances. You can read more from [authorization example](#authorization).

**Multiple original storages**

[Multiple original storages](#multiple-original-storages) allows you to use different original storage for one proxy-storage.
For example, [store text files in GridFs and other file types in filesystem](#original-storage-by-file-type).

**Fallback**

[Fallback](#fallback) proxy-storage is an example of [multiple original storages](#multiple-original-storages). It comes
out of the box and helps to implement fallback, for example, from filesystem storage to GridFS
on `IOError` or `OSError` exceptions.

### Proxy-storage

Django-proxy-storage is a simple subclass of standard django `Storage` class. It doesn't break default
django storage interface and that's why it's is convenient to use it with [model file fields](#model-fields).

#### Base class

`ProxyStorageBase` is a base class for every proxy-storage object. Subclasses should set next attributes:

* **original_storage** - django storage instance that will be used as an original storage.
Every action of proxy-storage (`save`, `open`, `exists`, `delete`) will be proxied to this storage.
* **meta_backend** - instance of [meta-backend](#meta-backend) that will be used for storing information about files from
original storages for current proxy-storage.

You can see implementation example from [quick start](#quick-start).

#### How it works

What happens when `save` method called:

    >>> storage = FileSystemProxyStorage()
    >>> storage.save('hello.txt', ContentFile('world'))
    '/tmp/hello_1.txt'

* Save file to original storage
* Try to save meta information to [meta-backend](#meta-backend) with `path` equals original storage path `/tmp/hello.txt`
* If there is already existing information with passed `path`,
then iterate while not existing path found (for example `/tmp/hello_1.txt`)
* Create meta information with unique path
* Return path (`/tmp/hello_1.txt`)

`save` method has additional argument `original_storage_path`.
If it passed then no saving to original storage would be performed. Look at [migration example](#file-field-migration).

What happens when `exists` method called:

    >>> storage = FileSystemProxyStorage()
    >>> storage.save('hello.txt', ContentFile('world'))
    '/tmp/hello_1.txt'
    >>> storage.exists('/tmp/hello_1.txt')
    True

* Try to find [meta-backend object](#meta-backend-object) with `path` equals `/tmp/hello_1.txt`
* If it exists return `True`
* If it doesn't exist return `False`

What happens when `open` method called:

    >>> storage = FileSystemProxyStorage()
    >>> storage.save('hello.txt', ContentFile('world'))
    '/tmp/hello_1.txt'
    >>> storage.open('/tmp/hello_1.txt')
    <File: /tmp/hello.txt>

* Try to find [meta-backend object](#meta-backend-object) with `path` equals `/tmp/hello_1.txt`
* If it doesn't exist raise `IOError`
* If it exists call original storage `open` method with `path` equals
[meta-backend object's](#meta-backend-object) value by key `original_storage_path` and return response

What happens when `delete` method called:

    >>> storage = FileSystemProxyStorage()
    >>> storage.save('hello.txt', ContentFile('world'))
    '/tmp/hello_1.txt'
    >>> storage.delete('/tmp/hello_1.txt')

* Try to find [meta-backend object](#meta-backend-object) with `path` equals `/tmp/hello_1.txt`
* If it doesn't exist raise `IOError`
* If it exists call original storage `delete` method with `path` equals
[meta-backend object's](#meta-backend-object) value by key `original_storage_path`
* Remove [meta-backend object](#meta-backend-object) with `path` equals `/tmp/hello.txt`

For retrieving original storage you should use `get_original_storage` method. Don't use `original_storage` attribute
directly:

    >>> from yourapp.storages import FileSystemProxyStorage
    >>> proxy_storage = FileSystemProxyStorage()
    >>> proxy_storage.get_original_storage()


#### Multiple original storages

`MultipleOriginalStoragesMixin` adds ability to use more than one original storage. Those storages should be set as
`original_storages` attribute in format of an iterable (e.g., a list or tuple) consisting itself
of iterables of exactly two items - name of the original storage and storage itself. For example:

    # yourapp/storages.py
    from django.core.files.storage import FileSystemStorage
    from storages.backends.mongodb import GridFSStorage
    from proxy_storage.storages.base import (
        ProxyStorageBase,
        MultipleOriginalStoragesMixin
    )
    from proxy_storage.meta_backends.mongo import MongoMetaBackend
    from yourapp import get_mongo_db

    class FileSystemOrGridFSProxyStorage(MultipleOriginalStoragesMixin,
                                         ProxyStorageBase):
        original_storages = (
            ('file_system', FileSystemStorage(location='/var/files/')),
            ('gridfs', GridFSProxyStorage()),
        )
        meta_backend = MongoMetaBackend(
            database=get_mongo_db(),
            collection='meta_backend_collection'
        )

Dont forget to register it in settings:

    # settings.py
    PROXY_STORAGE = {
        'PROXY_STORAGE_CLASSES': {
            'file_system_or_gridfs_proxy_storage':
                'yourapp.storages.FileSystemOrGridFSProxyStorage',
        }
    }

Let's try it:

    >>> from yourapp.storages import FileSystemOrGridFSProxyStorage
    >>> storage = FileSystemOrGridFSProxyStorage()


By default it saves to first original storage which is `file_system`:

    >>> storage.save('hello.txt', ContentFile('world'))
    '/tmp/hello.txt'


But you can specify `using` argument to force usage of specific original storage:

    >>> storage.save('hello.txt', ContentFile('world'), using='gridfs')
    '/hello.txt'

If no original storage forced to be used with `using` attribute then first by ordering original storage is used
in operations.

`MultipleOriginalStoragesMixin` adds to [meta-backend object](#meta-backend-object) `original_storage_name` key. Value
of this key contains original storage name which used for
determining original storage from `original_storages` attribute:

    >>> proxy_storage = FileSystemOrGridFSProxyStorage()
    >>> meta_backend_obj = proxy_storage.meta_backend.get('/tmp/hello.txt')
    {
        '_id': ObjectId('53d37e2856c02c1657b8ef92'),
        'proxy_storage_name': 'file_system_or_gridfs_proxy_storage',
        'path': '/tmp/hello.txt',
        'original_storage_path': 'hello.txt',
        'original_storage_name': 'file_system'
    }

To get original storage for [meta-backend object](#meta-backend-object) you should send it to `get_original_storage` method:

    >>> proxy_storage = FileSystemOrGridFSProxyStorage()
    >>> meta_backend_obj = proxy_storage.meta_backend.get('/tmp/hello.txt')
    >>> proxy_storage.get_original_storage(meta_backend_obj)
    <django.core.files.storage.FileSystemStorage object at 0x2c74fd0>

You can read about usage of multiple original storages for [storing text files in GridFs and other file types in filesystem](#original-storage-by-file-type).

#### Fallback

`FallbackProxyStorageMixin` allows you to specify [multiple original storages](#multiple-original-storages) and set
fallback exceptions that should be caught when `save` method is called.
If exception is caught then next original storage tried to be used.

Every original storage must be mixed in with `OriginalStorageFallbackMixin` that adds
interfaces for adding fallback exceptions.

    from django.core.files.storage import FileSystemStorage
    from storages.backends.mongodb import GridFSStorage
    from proxy_storage.storages.fallback import OriginalStorageFallbackMixin
    from pymongo.errors import AutoReconnect

    class FileSystemFallbackStorage(OriginalStorageFallbackMixin,
                                    FileSystemStorage):
        fallback_exceptions = (IOError, OSError)

    class GridFSFallbackStorage(OriginalStorageFallbackMixin,
                                FileSystemStorage):
        fallback_exceptions = (AutoReconnect,)

Let's add those storages to proxy-storage:

    # yourapp/storages.py
    from proxy_storage.storages.base import ProxyStorageBase
    from proxy_storage.storages.fallback import (
        OriginalStorageFallbackMixin,
        FallbackProxyStorageMixin
    )

    class ProxyStorageWithFallback(FallbackProxyStorageMixin,
                                          ProxyStorageBase)
        original_storages = [
            ('file_system', FileSystemFallbackStorage(location='/tmp/dir/')),
            ('gridfs', GridFSFallbackStorage()),
        ]

Let's try it when there is no problems with filesystem:

    >>> from yourapp.storages import FileSystemProxyStorageWithFallback
    >>> storage = FileSystemProxyStorageWithFallback()
    >>> storage.save('hello.txt', ContentFile('world'))
    '/tmp/dir/hello.txt'
    >>> storage.meta_backend.get('/tmp/dir/hello.txt')['original_storage_name']
    'file_system'

Let's make from `/tmp/dir/` simple text file:

    $ rm -rf /tmp/dir/
    $ echo 'hello world' > /tmp/dir
    $ file /tmp/dir
    /tmp/dir: ASCII text

In this case `FileSystemStorage` usually raises `IOError("/tmp/dir exists and is not a directory")`, but we've registered
it in `fallback_exceptions`. `IOError` will be caught and next original storage will be used:

    >>> from yourapp.storages import FileSystemProxyStorageWithFallback
    >>> storage = FileSystemProxyStorageWithFallback()
    >>> storage.save('hello.txt', ContentFile('world'))
    '/hello.txt'
    >>> storage.meta_backend.get('/hello.txt')['original_storage_name']
    'gridfs'

If last original storage from `original_storages` raised exception
(no matter whether it registered in `fallback_exceptions` or not) then that exception would be raised.

For example if `file_system` storage raised registered exception and `gridfs` raised any exception then exception from
`gridfs` storage will not be caught:

    >>> proxy_storage = ProxyStorageWithFallback()
    >>> proxy_storage.save('hello.txt', ContentFile('world'))
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    pymongo.errors.AutoReconnect: Connection problem

### Meta-backend

Meta-backend is a main feature of django-proxy-storage. Meta-backend stores information
about files in original storages. Out of the box you can store it in [MongoDB](#mongo-meta-backend) or [ORM](#orm-meta-backend).

#### Meta-backend base class

The `proxy_storage.meta_backends.base.MetaBackendBase` class provides a standardized API for storing meta information,
along with a set of default behaviors that all other backends can inherit or override as necessary.

**get(path)**

Returns [meta-backend object](#meta-backend-object) instance by `path`. If there is no such object
raises `proxy_storage.meta_backends.base.MetaBackendObjectDoesNotExist` exception.

**delete(path)**

Deletes [meta-backend object](#meta-backend-object) instance referenced by `path`.

**update(path, update_data)**

Updates [meta-backend object](#meta-backend-object) instance referenced by `path`.

`update_data` argument must be dict.

**exists(path)**

Returns `True` if a [meta-backend object](#meta-backend-object) referenced by `path` already exists in the meta-backend,
or `False` if it doesn't.

#### Meta-backend object

Meta-backend object contains complete information about proxy-storage and original storage (names, paths, etc...).

It's subclass of `dict` with custom methods:

**get\_original\_storage()**

Returns used original storage instance.

**get\_proxy\_storage()**

Returns used proxy-storage instance.

**get\_original\_storage\_full\_path()**

Returns full file path for original storage.

Base meta-backend keeps next information:

* **proxy\_storage\_name** - name of used proxy-storage (from settings `PROXY_STORAGE['PROXY_STORAGE_CLASSES']` key)
* **path** - unique path for meta-backend
* **original\_storage\_path** - path for original storage

Example:

    {
        'proxy_storage_name': 'file_system_or_gridfs_proxy_storage',
        'path': '/tmp/hello.txt',
        'original_storage_path': 'hello.txt',
    }

You can read about [custom meta-backend data](#custom-meta-backend-data) for extending it with your custom data.

### Mongo meta-backend

`proxy_storage.meta_backends.mongo.MongoMetaBackend` is a subclass of [MetaBackendBase](#meta-backend-base-class).
This meta-backend must be initialized with next arguments:

* **database** - instance of [pymongo.database.Database](http://api.mongodb.org/python/current/api/pymongo/database.html#pymongo.database.Database)
class.
* **collection** - name of the collection where to store meta information

Example:

    from pymongo import MongoClient
    from proxy_storage.meta_backends.mongo import MongoMetaBackend

    mongo_meta_backend = MongoMetaBackend(
        database=MongoClient('localhost', 27017).db,
        collection='meta_backend_collection'
    )

`database` argument value could be callable:

    from pymongo import MongoClient
    from proxy_storage.meta_backends.mongo import MongoMetaBackend

    def get_mongo_db():
        return MongoClient('localhost', 27017).db

    mongo_meta_backend = MongoMetaBackend(
        database=get_mongo_db,
        collection='meta_backend_collection'
    )

#### Mongo meta-backend object

Has the same interface as [base meta-backend object](#meta-backend-object) but adds `_id` key that
contains [ObjectId](http://api.mongodb.org/python/current/api/bson/objectid.html#bson.objectid.ObjectId)
of current document.

    {
        '_id': ObjectId('53d6226d1c9eab4de712e78d'),
        'proxy_storage_name': 'file_system_or_gridfs_proxy_storage',
        'path': '/tmp/hello.txt',
        'original_storage_path': 'hello.txt',
    }

### ORM meta-backend

`proxy_storage.meta_backends.orm.ORMMetaBackend` is a subclass of [MetaBackendBase](#meta-backend-base-class).
This meta-backend must be initialized with next arguments:

* **model** - model class that will store meta information.

Django-proxy-storage provides base model class `ProxyStorageModelBase` for usage with ORM meta-backend.
You must inherit from it in your application:

    # yourapp/models.py
    from proxy_storage.meta_backends.orm import ProxyStorageModelBase

    class ProxyStorageModel(ProxyStorageModelBase):
        pass

*If you use [django-south](http://south.readthedocs.org/en/latest/) or django>=1.7 don't
forget to create and apply migration.*

Let's use that model for proxy-storage:

    from proxy_storage.meta_backends.orm import ORMMetaBackend
    from yourapp.models import ProxyStorageModel

    orm_meta_backend = ORMMetaBackend(model=ProxyStorageModel)

#### ORM meta-backend object

Has the same interface as [base meta-backend object](#meta-backend-object) but adds `id` key that
contains model's primary key.

    {
        'id': 10,
        'proxy_storage_name': 'file_system_or_gridfs_proxy_storage',
        'path': '/tmp/hello.txt',
        'original_storage_path': 'hello.txt',
    }

#### Content object field

If you want to use [content object field context](#content-object-field-context) you must add [generic relations](https://docs.djangoproject.com/en/dev/ref/contrib/contenttypes/#generic-relations)
fields to meta-backends's model class. That could be done by mixing in `ContentObjectFieldMixin` to your meta-backends's model class:

    # yourapp/models.py
    from proxy_storage.meta_backends.orm import (
        ProxyStorageModelBase,
        ContentObjectFieldMixin
    )

    class ProxyStorageModel(ContentObjectFieldMixin,
                            ProxyStorageModelBase):
        pass

#### Original storage name

If you want to use [multiple original storages](#multiple-original-storages)
or [fallback proxy-storage](#fallback) then you must add field for determining used original storage.
That could be done by mixing in `OriginalStorageNameMixin` to your meta-backends's model class:

    # yourapp/models.py
    from proxy_storage.meta_backends.orm import (
        ProxyStorageModelBase,
        OriginalStorageNameMixin
    )

    class ProxyStorageModel(OriginalStorageNameMixin,
                            ProxyStorageModelBase):
        pass

### Model fields

Django-proxy-storage doesn't break default django storage interface and it could be used with standard django
[FileField](https://docs.djangoproject.com/en/dev/ref/models/fields/#filefield):

    # yourapp/models.py
    from django.db import models
    from yourapp.storages import GridFSProxyStorage

    class JobApply(models.Model):
        user = models.ForeignKey(User)
        resume = models.FileField(storage=GridFSProxyStorage())

#### Content object field context

*If you use this feature with [ORM meta-backend](#orm-meta-backend) don't
forget to add [ContentObjectFieldMixin](#content-object-field) to your meta-backends's model class.*

For [authorization](#authorization) purposes it's helpful to store content object and field name information. It could
be done by using `ProxyStorageFileField`:

    # yourapp/models.py
    from django.db import models
    from proxy_storage.db.fields import ProxyStorageFileField
    from yourapp.storages import GridFSProxyStorage

    class JobApply(models.Model):
        user = models.ForeignKey(User)
        resume = ProxyStorageFileField(storage=GridFSProxyStorage())

Let's see how [meta-backend object](#meta-backend-object) changed:

    >>> from yourapp.storages import GridFSProxyStorage
    >>> from yourapp.models import JobApply
    >>> from django.contrib.auth.models import User
    >>> from django.core.files.base import ContentFile

    >>> messi_apply = JobApply(user=User.objects.get(username='messi'))
    >>> messi_apply.resume.save(
    ...     '/messi_resume.txt',
    ...     ContentFile('Currently i am playing in Barcelona')
    ... )  # saved to GridGS with path '/messi_resume.txt'

    >>> meta_backend = GridFSProxyStorage().meta_backend
    >>> meta_backend.get('/messi_resume.txt')
    {
        'id': 1,
        'proxy_storage_name': 'gridfs_proxy_storage',
        'path': '/messi_resume.txt',
        'original_storage_path': '/messi_resume.txt',
        'content_type_id': 2,  # Content type of JobApply model,
        'object_id': 100,  # id of messi_apply instance
        'field': 'resume'
    }

You can read how `content_type_id`, `object_id` and `field` context could
be used for [authorization purposes](#authorization).

### Examples

*All code snippets from this section hadn't been tested and provided only for example purposes.*

#### Authorization

*You can read more about serving authenticated static files from [this article](http://zacharyvoase.com/2009/09/08/sendfile/).
It describes in general how it should be done by web applications.
I encourage you to read it first and then continue reading this documentation.*

Usage of [content object field context](#content-object-field-context) provides great authorization facilities.

For our example we will have `JobApply` model which will store information about applied resumes.
This model will have four fields:

* **user** - who applied.
* **what\_you\_want** - what user wants to do at his new job.
* **resume** - for storing resume files. We will store it in GridFS and it could be accessed only by `JobApply` instance
owner or administrator.
* **avatar** - for storing avatar image files. We will store it in filesystem and it could be accessed by anybody.

First of all let's implement proxy-storages:

    # yourapp/storages.py
    from django.core.files.storage import FileSystemStorage
    from storages.backends.mongodb import GridFSStorage
    from proxy_storage.storages.base import ProxyStorageBase
    from proxy_storage.meta_backends.mongo import MongoMetaBackend
    from pymongo import MongoClient

    meta_backend = MongoMetaBackend(
        database=MongoClient('localhost', 27017).db,
        collection='meta_backend_collection'
    )

    class FileSystemProxyStorage(ProxyStorageBase):
        meta_backend = meta_backend
        original_storage = FileSystemStorage(location='/var/files/')

    class GridFSProxyStorage(ProxyStorageBase):
        meta_backend = meta_backend
        original_storage = GridFSStorage()

`GridFSStorage` storage is configured to use `gridfs_db` database and `files` collection in it.

Don't forget to register proxy-storages in settings:

    # settings.py
    PROXY_STORAGE = {
        'PROXY_STORAGE_CLASSES': {
            'file_system_proxy_storage':
                'yourapp.storages.FileSystemProxyStorage',
            'gridfs_proxy_storage':
                'yourapp.storages.GridFSProxyStorage',
        }
    }

Let's implement models:

    # yourapp/models.py
    from django.db import models
    from django.contrib.auth.models import User
    from yourapp.storages import FileSystemProxyStorage, GridFSProxyStorage
    from proxy_storages.db.fields import ProxyStorageFileField

    class JobApply(models.Model):
        user = models.ForeignKey(User)
        what_you_want = models.CharField(max_length=255)
        resume = ProxyStorageFileField(storage=GridFSProxyStorage())
        avatar = ProxyStorageFileField(storage=FileSystemProxyStorage())

For serving files we will use nginx and [X-Accel-Redirect](http://wiki.nginx.org/X-accel) header. Let's configure nginx:

    server {
        listen 80;
        server_name yoursite.com

        location / {
            proxy_pass http://unix:/var/run/gunicorn.socket;
        }

        location /serve-from-fs/ {
            internal;
            root /var/files/;
        }

        # https://github.com/mdirolf/nginx-gridfs
        location /serve-from-gridfs/ {
            internal;
            gridfs gridfs_db root_collection='files';
        }
    }

Files from filesystem will be served through `/serve-from-fs/` location and files from GridFS will be served through
`/serve-from-gridfs/` location.

Let's create apply from Messi:

    >>> from yourapp.models import JobApply
    >>> from django.auth.contrib.models import User
    >>> from django.core.files.base import ContentFile

    >>> messi = User.objects.get(username='messi')
    >>> messi_apply = JobApply(
    ...     user=messi,
    ...     what_you_want='I want to play like Diego'
    ... )
    >>> messi_apply.resume.save(
    ...     '/messi_resume.txt',
    ...     ContentFile('Currently i am playing in Barcelona')
    ... )  # saved to GridGS with path "/messi_resume.txt"
    >>> messi_apply.avatar.save(
    ...     'messi_avatar.jpg',
    ...     open('/some/dir/messi_avatar.jpg')
    ... )  # saved to filesystem with path "/var/files/messi_avatar.jpg"


Next step is to implement view and configure routing.

    # yourapp/views.py
    from django.http import HttpResponse

    def files(request):
        return HttpResponse('hello world')

Routing:

    # yourapp/urls.py
    from django.conf.urls import url

    from yourapp import views

    urlpatterns = [
        url(r'^files/$', views.files, name='files')
    ]

Let's describe how we will serve files:

* Request comes to `http://yoursite.com/files/?path=/some/file.txt`
* If `/some/file.txt` doesn't exist the return response with `404` status code
* If client doesn't have access to `/some/file.txt` then return error with `403` status code
* If client has access to `/some/file.txt` then serve it
* If `/some/file.txt` is stored in filesystem then serve it from `/serve-from-fs/` nginx location
* If `/some/file.txt` is stored in GridFS then serve it from `/serve-from-gridfs/` nginx location

Let's do this:

    # yourapp/views.py
    from django.http import HttpResponse
    from django.contrib.contentypes.models import ContentType
    from yourapp.storages import meta_backend
    from yourapp.models import JobApply
    from proxy_storage.meta_backends.base import MetaBackendObjectDoesNotExist

    def files(request):
        path = request.GET.get('path')

        # trying to find meta backend object
        try:
            meta_backend_obj = meta_backend.get(path)
        except MetaBackendObjectDoesNotExist:
            return HttpResponse(status_code=404)

        # if content type is not JobApply, then don't try to serve file
        content_type = ContentType.objects.get(
            id=meta_backend_obj['content_type_id']
        )
        if content_type is not JobApply:
            return HttpResponse(status_code=404)

        job_apply = JobApply.objects.get(
            pk=meta_backend_obj['object_id']
        )

        has_access = False

        # allow access to 'avatar' for anybody
        if meta_backend_obj['field'] == 'avatar':
            has_access = True
        # check permission for resume
        elif meta_backend_obj['field'] == 'resume' :
            has_access = (
                request.user.is_authenticated() and (
                    request.user.is_staff or request.user == job_apply.user
                )
            )

        if has_access:
            response = HttpResponse(status_code=200)
            response['x-accel-redirect'] = get_x_accel_redirect(
                meta_backend_obj
            )
            return response
        else:
            return HttpResponse(status_code=403)

And finally we'll implement `get_x_accel_redirect` method that returns different redirection paths for different
original storages:

    # yourapp/views.py
    from django.core.files.storage import FileSystemStorage
    from storages.backends.mongodb import GridFSStorage

    def get_x_accel_redirect(meta_backend_obj):
        serve_path = meta_backend_obj.get_original_storage_full_path()
        original_storage = meta_backend_obj.get_original_storage()
        if isinstance(original_storage, FileSystemStorage):
            location = '/serve-from-fs'
        elif isinstance(original_storage, GridFSStorage):
            location = '/serve-from-gridfs'
        return location + serve_path

Providing that Messi has `messi` authentication key let's try to make requests to his resume and avatar
files:

    $ curl -I --cookie "sessionid=messi" \
           http://yoursite.com/files/?path=/messi_resume.txt
    HTTP/1.1 200 OK

    $ curl -I --cookie "sessionid=messi" \
           http://yoursite.com/files/?path=/var/files/messi_avatar.jpg
    HTTP/1.1 200 OK

Providing that Ronaldo has `ronaldo` authentication key let's try to make requests to messi's resume and avatar
files:

    $ curl -I --cookie "sessionid=ronaldo" \
           http://yoursite.com/files/?path=/messi_resume.txt
    HTTP/1.1 403 FORBIDDEN

    $ curl -I --cookie "sessionid=ronaldo" \
           http://yoursite.com/files/?path=/var/files/messi_avatar.jpg
    HTTP/1.1 200 OK

As you can see Ronaldo couldn't get messi's resume file but could get his avatar. Finally let's try to make requests
by administrator who has `admin` authentication key:

    $ curl -I --cookie "sessionid=admin" \
           http://yoursite.com/files/?path=/messi_resume.txt
    HTTP/1.1 200 OK

    $ curl -I --cookie "sessionid=admin" \
           http://yoursite.com/files/?path=/var/files/messi_avatar.jpg
    HTTP/1.1 200 OK

Yep, administrator has full access to both messi's resume and avatar files.

#### Original storage by file type

In this example we will implement proxy storage that stores:

* Text files in GridFs
* Other files in filesystem
* If `save` method forced to use exact original storage by providing `using` argument then store file in that original storage.

Let's do this:

    # yourapp/storages.py
    from django.core.files.storage import FileSystemStorage
    from storages.backends.mongodb import GridFSStorage
    from proxy_storage.storages.base import (
        ProxyStorageBase,
        MultipleOriginalStoragesMixin
    )
    from proxy_storage.meta_backends.mongo import MongoMetaBackend
    from yourapp import get_mongo_db

    class FileSystemOrGridFSProxyStorage(MultipleOriginalStoragesMixin,
                                         ProxyStorageBase):
        original_storages = (
            ('file_system', FileSystemStorage(location='/var/files/')),
            ('gridfs', GridFSProxyStorage()),
        )
        meta_backend = MongoMetaBackend(
            database=get_mongo_db(),
            collection='meta_backend_collection'
        )

        def save(self, name, content, original_storage_path=None, using=None):
            if not using:
                if name.endswith('.txt'):
                    using = 'gridfs'
                else:
                    using = 'file_system'
            return super(FileSystemOrGridFSProxyStorage, self).save(
                name=name,
                content=content,
                original_storage_path=original_storage_path,
                using=using
            )

#### Custom meta-backend data

Out of the box [meta-backend object](#meta-backend-object) contains only vital information for determining proxy-storage
and original storage. For example, what if you wanted to store next fields:

* **mime_type** - mime type of file for serving purposes
* **size** - file size
* **created_at** - date when file was created

Let's do this:

    # yourapp/storages.py
    import datetime
    from django.core.files.storage import FileSystemStorage
    from storages.backends.mongodb import GridFSStorage
    from proxy_storage.storages.base import ProxyStorageBase
    from proxy_storage.meta_backends.mongo import MongoMetaBackend
    from yourapp import get_mongo_db
    from yourapp.utils import (
        get_mime_type_from_content,
        get_size_from_content
    )

    class FileSystemProxyStorage(ProxyStorageBase):
        original_storage = FileSystemStorage(location='/var/files/')
        meta_backend = MongoMetaBackend(
            database=get_mongo_db(),
            collection='meta_backend_collection'
        )

        def get_data_for_meta_backend_save(self,
                                           path,
                                           original_storage_path,
                                           original_name,
                                           content):
            super_instance = super(FileSystemProxyStorage, self)
            data = super_instance.get_data_for_meta_backend_save(
                path=path,
                original_storage_path=original_storage_path,
                original_name=original_name,
                content=content
            )
            data.update({
                'mime_type': get_mime_type_from_content(content),
                'size': get_size_from_content(content),
                'created_at': datetime.datetime.utcnow()
            })
            return data

        def size(self, name):
            return self.meta_backend.get(path=name)['size']

        def created_time(self, name):
            return self.meta_backend.get(path=name)['created_at']

*If you use [ORM meta-backend](#orm-meta-backend) don't forget to add `mime_type`, `size` and `created_at` fields
to your model class.*

Let's use it:

    >>> from yourapp.storages import FileSystemProxyStorage
    >>> proxy_storage = FileSystemProxyStorage()
    >>> proxy_storage.save('hello.txt', ContentFile('world'))
    '/var/files/hello.txt'
    >>> proxy_storage.meta_backend.get('/var/files/hello.txt')
    {
        '_id': ObjectId('53d37e2856c02c1657b8ef92'),
        'proxy_storage_name': 'file_system_proxy_storage',
        'path': '/tmp/files/hello.txt',
        'original_storage_path': 'hello.txt',
        'mime_type': 'text/plain',
        'size': 5,
        'create_at': datetime.datetime(2014, 7, 28, 12, 31, 2, 132269)
    }

    >>> proxy_storage.size('/var/files/hello.txt')
    5

    >>> proxy_storage.created_time('/var/files/hello.txt')
    datetime.datetime(2014, 7, 28, 12, 31, 2, 132269)


#### File field migration

Imagine you already have model with `FileField` that uses simple django storage:

    # yourapp/models.py
    from django.db import models
    from django.core.files.storage import FileSystemStorage

    class JobApply(models.Model):
        resume = models.FileField(storage=FileSystemStorage('/var/files/'))

And there are already data in database with files:

    >>> from yourapp.models import JobApply
    >>> JobApply.objects.all().values_list('resume', flat=True)
    ['messi_resume.txt', 'ronaldo_resume.txt', 'muller_resume.txt']

For migration to proxy-storage you should create it:

    # yourapp/storages.py
    from django.core.files.storage import FileSystemStorage
    from proxy_storage.storages.base import ProxyStorageBase
    from proxy_storage.meta_backends.mongo import MongoMetaBackend
    from yourapp import get_mongo_db

    class FileSystemProxyStorage(ProxyStorageBase):
        original_storage = FileSystemStorage('/var/files/')
        meta_backend = MongoMetaBackend(
            database=get_mongo_db(),
            collection='meta_backend_collection'
        )

Use it in model:

    # yourapp/models.py
    from django.db import models
    from yourapp.storages import FileSystemProxyStorage

    class JobApply(models.Model):
        resume = models.FileField(storage=FileSystemProxyStorage())

And add data to [meta-backend](#meta-backend):

    >>> from yourapp.models import JobApply
    >>> from yourapp.storages import FileSystemProxyStorage

    >>> proxy_storage = FileSystemProxyStorage()
    >>> for job_apply in JobApply.objects.all():
    ...    file_name = str(job_apply.resume)
    ...    new_file_name = proxy_storage.save(
    ...        name=file_name,
    ...        content=job_apply.resume.open(),
    ...        original_storage_path=file_name
    ...    )
    ...    JobApply.objects.filter(pk=new_file_name.id).update(
    ...        resume=new_file_name
    ...    )

Let's see how model data changed:

    >>> from yourapp.models import JobApply
    >>> JobApply.objects.all().values_list('resume', flat=True)
    ['/var/files/messi_resume.txt',
     '/var/files/ronaldo_resume.txt',
     '/var/files/muller_resume.txt']

And meta-backend data:

    >>> from yourapp.storages import FileSystemProxyStorage
    >>> meta_backend = FileSystemProxyStorage().meta_backend
    >>> meta_backend.get('/var/files/messi_resume.txt')
    {
        '_id': ObjectId('53d37e2856c02c1657b8ef92'),
        'proxy_storage_name': 'file_system_proxy_storage',
        'path': '/var/files/hello.txt',
        'original_storage_path': 'hello.txt',
    }

### Settings

Configuration for Django-proxy-storage is all namespaced inside a single Django setting, named `PROXY_STORAGE`.

For example your project's `settings.py` file might include something like this:

    PROXY_STORAGE = {
        'PROXY_STORAGE_CLASSES': {
            'file_system_proxy_storage':
                'yourapp.storages.FileSystemProxyStorage',
        }
    }


#### Accessing settings

If you need to access the values of Django-proxy-storage settings in your project, you should use the `proxy_storage_settings` object. For example:

    from proxy_storage.settings import proxy_storage_settings

    print proxy_storage_settings.PROXY_STORAGE_CLASSES

### Release notes

Release notes for Django-proxy-storage

#### 0.1.1

*July 30, 2014*

* [Fixed #1](https://github.com/chibisov/django-proxy-storage/issues/1). Meta-backend object's
`get_original_storage_full_path` didn't send path attribute

#### 0.1.0

*July 29, 2014*

* Initial release