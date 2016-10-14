# -*- coding: utf-8 -*-

import os

from setuptools import setup, find_packages
from distutils.core import Command


here = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file
with open(os.path.join(here, 'README.rst')) as f:
    long_description = f.read()


class DjangoCommand(Command):

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from django.conf import settings
        settings.configure(
            INSTALLED_APPS=(
                'django.contrib.auth',
                'django.contrib.admin',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.messages',
                'django.contrib.staticfiles',
                'powerpages',
            ),
            SECRET_KEY='AAA',
            DATABASES={
                'default': {
                    'NAME': ':memory:',
                    'ENGINE': 'django.db.backends.sqlite3'
                }
            },
            # TODO: MIDDLEWARE for 1.10
            MIDDLEWARE_CLASSES=(
                'django.middleware.security.SecurityMiddleware',
                'django.contrib.sessions.middleware.SessionMiddleware',
                'django.middleware.common.CommonMiddleware',
                'django.middleware.csrf.CsrfViewMiddleware',
                'django.contrib.auth.middleware.AuthenticationMiddleware',
                'django.contrib.messages.middleware.MessageMiddleware',
                'django.middleware.clickjacking.XFrameOptionsMiddleware',
                'django.middleware.locale.LocaleMiddleware',
            ),
            LANGUAGE_CODE='en-us',
            ROOT_URLCONF='powerpages.tests.urls',
            TEMPLATES=[
                {
                    'BACKEND':
                    'django.template.backends.django.DjangoTemplates',
                    'OPTIONS': {
                        'loaders': [
                            'django.template.loaders.filesystem.Loader',
                            'django.template.loaders.app_directories.Loader',
                            # Database template loader for powerpages app
                            'powerpages.loader.WebsiteLoader',
                        ],
                        'context_processors': [
                            'django.template.context_processors.debug',
                            'django.template.context_processors.request',
                            'django.contrib.auth.context_processors.auth',
                            'django.contrib.messages.context_processors.messages',
                        ]
                    },
                },
            ]
        )
        import django
        django.setup()
        self._run()

    def _run(self):
        raise NotImplementedError


class Test(DjangoCommand):

    def _run(self):
        from django.core.management import call_command
        call_command('test', 'powerpages')


class MakeMigrations(DjangoCommand):

    def _run(self):
        from django.core.management import call_command
        call_command('makemigrations', 'powerpages')


setup(
    name='django-powerpages',
    version='0.0.2',
    description=(
        'Developer-friendly, simple CMS for Django, "flatpages on steroids".'
    ),
    long_description=long_description,
    url='https://github.com/Open-E-WEB/django-powerpages',
    author='Open-E, Inc.',
    author_email='',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Environment :: Web Environment',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Framework :: Django :: 1.9',
        'Topic :: Internet :: WWW/HTTP',
    ],
    keywords='django cms web',
    install_requires=[
        'PyYAML==3.11',
    ],
    packages=find_packages(),
    include_package_data=True,
    cmdclass={'test': Test, 'makemigrations': MakeMigrations},
)
