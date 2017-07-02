#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
from io import open

from setuptools import setup

try:
    from pypandoc import convert

    def read_md(f):
        return convert(f, 'rst').replace('\r', '')
except ImportError:
    print(
        "warning: pypandoc module not found, could not convert Markdown to RST"
    )

    def read_md(f):
        return open(f, 'r', encoding='utf-8').read()


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [
        dirpath
        for dirpath, dirnames, filenames in os.walk(package)
        if os.path.exists(os.path.join(dirpath, '__init__.py'))
    ]


def get_package_data(package):
    """
    Return all files under the root package, that are not in a
    package themselves.
    """
    walk = [
        (dirpath.replace(package + os.sep, '', 1), filenames)
        for dirpath, dirnames, filenames in os.walk(package)
        if not os.path.exists(
            os.path.join(dirpath, '__init__.py')
        )
    ]

    filepaths = []
    for base, filenames in walk:
        filepaths.extend([
            os.path.join(base, filename) for filename in filenames
        ])
    return {package: filepaths}


version = "0.1.4"

setup(
    name='fitness',
    version=version,
    license='BSD',
    description='Fitness Module',
    long_description='Fitness Module',
    author='Karl Odie',
    author_email='karlodie@gmail.com',
    packages=get_packages('fitness'),
    package_data=get_package_data('fitness'),
    install_requires=[
        'django',
        'django-bootstrap3',
        'djangorestframework',
        'pygal',
        'python-dateutil',
    ],
    setup_requires=['pytest-runner>=2.9'],
    tests_require=[
        'pytest>=3.0.4',
        'pytest-base-url>=1.2',
        'pytest-django>=3.0',
        'pytest-cov>=2.4',
        'pytest-flake8>=0.8.1',
        'pytest-isort>=0.1',
        'pytest-selenium>=1.6',
        'pytest-mock',
        'factory_boy',
    ],
    zip_safe=False,
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
