#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup
import re
import os
import sys


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.match("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [dirpath
            for dirpath, dirnames, filenames in os.walk(package)
            if os.path.exists(os.path.join(dirpath, '__init__.py'))]


def get_package_data(package):
    """
    Return all files under the root package, that are not in a
    package themselves.
    """
    walk = [(dirpath.replace(package + os.sep, '', 1), filenames)
            for dirpath, dirnames, filenames in os.walk(package)
            if not os.path.exists(os.path.join(dirpath, '__init__.py'))]

    filepaths = []
    for base, filenames in walk:
        filepaths.extend([os.path.join(base, filename)
                          for filename in filenames])
    return {package: filepaths}


version = get_version('proxy_storage')


if sys.argv[-1] == 'publish':
    os.system("python setup.py sdist upload")
    # os.system("python setup.py bdist_wheel upload")  # todo
    print("You probably want to also tag the version now:")
    print("  git tag -a %s -m 'version %s'" % (version, version))
    print("  git push --tags")
    sys.exit()


setup(
    name='django-proxy-storage',
    version=version,
    url='http://github.com/chibisov/django-proxy-storage',
    download_url='https://pypi.python.org/pypi/django-proxy-storage/',
    license='BSD',
    description='Proxy storage for any Django storage',
    long_description=('Provides simple Django storage that proxies every operation to '
                      'original storage and saves meta information about files to database.'),
    author='Gennady Chibisov',
    author_email='web-chib@ya.ru',
    packages=get_packages('proxy_storage'),
    package_data=get_package_data('proxy_storage'),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
    ]
)