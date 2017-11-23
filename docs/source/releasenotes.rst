.. _releasenotes:

Release Notes
=============

4.0.0 (2017-11-23)
------------------

``4.0.0`` is a big milestone of upgrading Django to newer version and making
Nitrate is compatible with Python 3 from ``3.4`` to ``3.6``. Dependent packages
are upgraded to proper version as well.

Regarding Python 2, ``2.6`` is dropped. Only ``2.7`` is supported.

Database maintenance has been changed totally. It now depends on Django
``migrate`` command to initialize and migrate database.

.. WARNING::
  Technically, it should be ok to run ``4.0.0`` with existing Nitrate database,
  but please do not run migrations from your current database, which is not
  supported.

For full change log, please see also ``CHANGELOG.rst``.
