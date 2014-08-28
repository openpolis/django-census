=============
django-census
=============

.. image:: https://badge.fury.io/py/django-census.png
    :target: https://badge.fury.io/py/django-census

.. image:: https://travis-ci.org/openpolis/django-census.png?branch=master
    :target: https://travis-ci.org/openpolis/django-census

.. image:: https://coveralls.io/repos/openpolis/django-census/badge.png?branch=master
    :target: https://coveralls.io/r/openpolis/django-census?branch=master

Django application to manage questions and answers

Documentation
-------------

The full documentation is at https://django-census.readthedocs.org.

Quickstart
----------

Install django-census::

    pip install django-census

Then use it in a project::

    import django-census

Features
--------

* Manage Question status (draft, published, completed and archived)
* Optional Answers
* Signals for user reply and question status change
* Support for custom user model
* Localized (en, it)
* Admin views