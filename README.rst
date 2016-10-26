django-powerpages
=================

.. image:: https://api.travis-ci.org/Open-E-WEB/django-powerpages.svg?branch=master
   :target: https://travis-ci.org/Open-E-WEB/django-powerpages
.. image:: https://img.shields.io/pypi/v/django-powerpages.svg
   :target: https://pypi.python.org/pypi/django-powerpages
.. image:: https://coveralls.io/repos/github/Open-E-WEB/django-powerpages/badge.svg?branch=master
   :target: https://coveralls.io/github/Open-E-WEB/django-powerpages?branch=master


Developer-friendly, simple CMS for Django, "flatpages on steroids".


Features
--------

- edit pages in Admin using syntax highlighting - HTML, CSS, JavaScript, Django template language
- edit pages as files using your favourite text editor or IDE
- on demand synchronization of pages between database and file system using Django commands
- integration with Django's template system
- attach custom server-side logic to a page through configurable *Page Processors*
- sitemap.xml


Installation
------------

Install package using pip:

.. code-block:: python

   pip install django-powerpages
   

Add ``'powerpages'`` to ``INSTALLED_APPS`` in your settings module:

.. code-block:: python

   INSTALLED_APPS = (
       ...
       'powerpages',
   )

Define ``POWER_PAGES`` setting:

.. code-block:: python

   POWER_PAGES = {
       # absolute path to directory, where page files are located:
       'SYNC_DIRECTORY': '/path/to/directory/'
   }

Include app's URLs at the end of your urlconf:

.. code-block:: python

   urlpatterns = [
       ...
       url(r'', include('powerpages.urls', namespace='powerpages')),
   ]

Run migrations:

.. code-block:: python

   python manage.py migrate


Usage
-----


Admin screenshots:
~~~~~~~~~~~~~~~~~~

.. image:: powerpages-scr-01.png

.. image:: powerpages-scr-02.png


Edit pages using Admin
~~~~~~~~~~~~~~~~~~~~~~

Admin interface allows to edit pages using the following fields:

- *URL* - unique address of every page
- *Alias* - optional code name for page to be used to resolve it's URL address
- *Title*, *Description*, *Keywords* - convenience fields to work with meta-tags
- *Template* - page's content as a Django template source
- *Page Processor* and *Page Processor Config* - options to assign and customize server-side logic

URL addresses of pages can be reversed in templates by using ``{% page_url alias %}``.
This template tag can also reverse URLs of regular Django views.

Page templates work as regular Django's templates with few modifications:

1. ``{% extends ... %}`` tag should not be used:

- by default each template inherits from template of parent page
- parent template can be overwritten by providing ``base template`` option to the page processor config
 
2. ``{% load ... %}`` tag is not necessary:

- template tag libraries from ``settings.POWER_PAGES['TAG_LIBRARIES']`` are loaded automatically
- additional libraries may be provided using ``tag libraries`` in page processor config

*Page Processor* field allows to select a Python class responsible for processing requests for current page.
Page processor can be configured using YAML config in *Page Processor Config* field.
Default value, ``powerpages.DefaultPageProcessor`` just renders page content and returns the output as ``200 OK`` response.
Other predefined options are:

- ``powerpages.RedirectProcessor`` - creates ``301 Moved Permanently`` or ``302 Found`` response depending on boolean ``permanent`` parameter. Redirect location is provided by URL (parameter ``to url``), view name (``to name``) or Page alias (``to alias``).
- ``powerpages.NotFoundProcessor`` - generates ``404 Not Found`` response.

Example configuration of default page processor:

.. code-block:: python

   base template: myapp/base.html
   context processors:
   - myapp.context_processors.context
   tag libraries:
   - myapp_tags
   headers: {x-magic-id: '42'}
   cache: 300
   cache for user: true
   sitemap: false

To define a custom page processor you may create a subclass of ``DefaultPageProcessor``
inside ``page_processors.py`` file in your app:

.. code-block:: python

   # myapp/page_processors.py
   from powerpages.page_processors import DefaultPageProcessor
   from powerpages.page_processor_registry import register
   
   class MyPageProcessor(DefaultPageProcessor):
   
        def process_request(self, request, extra_context=None):
            """Process a request and create HTTP Response."""
            # Put your custom view logic here
   
   register(MyPageProcessor)


Browse website in "edit mode"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Button "Edit mode" in Admin allows to show information about current page while browsing the website.
User enables "Edit mode" for current session in Admin using *Edit mode* button.
This mode works only if template tag ``{% current_page_info %}`` has been added to the template source.


File-Database Synchronization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Export pages from database to file system is done by ``website_dump`` command.
All pages are saved as structure of files and directories inside ``settings.POWER_PAGES['SYNC_DIRECTORY']``.
Exported pages can be modified using text editor and later loaded again into the database.

.. code-block:: python

   python manage.py website_dump

Example structure of output directory:

.. code-block:: python

   _index_.page
   about-us/_index_.page
   about-us/contact.page
   download.page
   robots.txt

Each of dumped files has the following structure:

.. code-block:: python

   {
      ... page fields as JSON
   }
   ## TEMPLATE SOURCE: ##
   ... template content (plain text)

Import pages from directory into database is done using ``website_load`` command.

.. code-block:: python

   python manage.py website_load

Both website commands accept a variety of options to tweak their behaviour.
For the full list of options, use ``--help``.


XML Sitemaps
~~~~~~~~~~~~

``django-powerpages`` comes with a system for defining XML Sitemaps (alternative to ``django.contrib.sitemaps``).
By default, all accessible pages are listed as URLs in ``sitemap.xml``.
To remove a page from the sitemap user may add the following option to page processor config:

.. code-block:: python

   sitemap: false


``sitemap`` option may be used to modify page's sitemap params:

.. code-block:: python

   sitemap: {changefreq: 'daily', priority: 0.9}

Default values for ``changefreq`` and ``priority`` for all URLs can be set using ``settings.POWER_PAGES``:

.. code-block:: python

   POWER_PAGES = {
       # (...)
       'SITEMAP_DEFAULT_CHANGEFREQ': 'weekly',
       'SITEMAP_DEFAULT_PRIORITY': 0.7,
   }

To add custom URLs from your app to the sitemap you may define and register
a subclass of ``Sitemap`` or ``ModelSitemap`` class inside ``sitemap.py`` file in your app:

.. code-block:: python

   # myapp/sitemap.py
   from powerpages import sitemap_config
   from myapp.models import MyModel
   
   class MyModelSitemap(sitemap_config.ModelSitemap):
       """Sitemap config for Storage Powered by Open-E document files"""
       queryset = MyModel.objects.all()

   class MyStaticSitemap(sitemap_config.Sitemap):
       items = (
           {'location': sitemap_config.NamedURL('myview')},
           {'location': sitemap_config.NamedURL('myview2', param='value')}
       )

   sitemap_config.sitemaps.add(MyModelSitemap)
   sitemap_config.sitemaps.add(MyStaticSitemap)


Requirements
------------

Python: 2.7, 3.4, 3.5

Django: 1.9, 1.10
