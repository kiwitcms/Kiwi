.. _deployment:

Installing nitrate on RHEL6 with Apache and MySQL
=================================================

This deployment document presumes that you are running Red Hat Enterprise Linux
6. Of course, all deployment steps being described through this document also
apply to other Linux distributions, such as CentOS, openSUSE, or Debian.

This document aims to deployment within a server that will serve test case
management service to stuffs or customers. Therefore, all commands and
configuration are done with system Python interpreter and those configuration
files installed in the standard system directories, like the
``/etc/httpd/conf/httpd.conf``.

Installation
------------


Get source code
~~~~~~~~~~~~~~~

The Nitrate source code is available at:https://github.com/Nitrate/Nitrate

You can get the latest changes with git easily::

  git clone https://github.com/Nitrate/Nitrate.git
  git checkout --track [a proper tag or branch]

Install dependencies
~~~~~~~~~~~~~~~~~~~~

Install devel packages that should be installed first::

    sudo yum install gcc w3m python-devel mysql-devel krb5-devel libxml2-devel libxslt-devel

Install dependencies from ``requirements/mysql.txt``::

    sudo pip install -r requirements/mysql.txt

.. note::

    Alternatively you can use ``requirements/postgres.txt`` for PostgreSQL!

Install from source code
~~~~~~~~~~~~~~~~~~~~~~~~

After downloading the source code, go to the source code directory and
install this project with python setup.py::

  cd [nitrate_download_path]/nitrate
  sudo python setup.py install

Initialize database
-------------------

Database is required by Nitrate (and all of Django apps). Django ORM supports
many database backends, we recommend you to use MySQL.

Create database and user for nitrate in mysql::

    mysql> create database nitrate;
    mysql> GRANT all privileges on nitrate.* to nitrate@'%' identified by 'password';

Update settings/product.py::

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
            'NAME': 'nitrate',                      # Or path to database file if using sqlite3.
            # The following settings are not used with sqlite3:
            'USER': 'nitrate',
            'PASSWORD': 'password',
            'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
            'PORT': '',                      # Set to empty string for default.
        }
    }

Create tables through syncdb & migrate and create super user if needed::

    django-admin.py syncdb --settings=tcms.settings.product
    django-admin.py migrate --settings=tcms.settings.product

Load initial data::

    django-admin.py loaddata --settings=tcms.settings.product

Config Settings
---------------

First please go to nitrate root path, it's different based on your current OS.

Like on RHEL6.3, the root path is located in::

    /usr/lib/python2.6/site-packages/nitrate-3.8.6-py2.6.egg/tcms

As we plan to deploy an example server for nitrate, we can use product.py as the
default settings. After backed up the product.py, please modify
settings based on your custom configurations in settings/product.py.
For more information see :doc:`configuration`!


Use cache (Optional)
--------------------

You can use Django's cache framework to get better performance.

Refer to following docs for more details:

- https://docs.djangoproject.com/en/1.5/topics/cache/

- https://docs.djangoproject.com/en/1.5/ref/settings/#caches

Start the django app
--------------------

After upon steps is completed, now you can try to start the web server which is
a built-in development server provided by Django to test if the app can run
as expected. Run following command::

    django-admin.py runserver --settings=tcms.settings.product

Then try to use web browser to open ``http://localhost:8000/`` to verify the
working status of this web service.


Install Apache & mod_wsgi
-------------------------

Install httpd & mod_wsgi::

    sudo yum install httpd mod_wsgi

Create upload dir
~~~~~~~~~~~~~~~~~

Create upload dir and change dir own & group to apache::

    sudo mkdir -p /var/nitrate/uploads
    sudo chown apache:apache /var/nitrate/uploads

Collect static files
~~~~~~~~~~~~~~~~~~~~

The default directory to store static files is `/var/nitrate/static`, you can
modify it by changing `STATIC_ROOT` setting in
`/path/to/nitrate/tcms/settings/product.py`.

Run following command to collect static files::

    sudo django-admin.py collectstatic --settings=tcms.settings.product

Reference: https://docs.djangoproject.com/en/1.5/howto/static-files/deployment/


Deploy with Apache
~~~~~~~~~~~~~~~~~~

Deploying Django projects with Apache and mod_wsgi is the recommended way to get
them into production.

Create wsgi.conf in /etc/httpd/conf.d/ which include one line::

    LoadModule wsgi_module modules/mod_wsgi.so

To build a production server with Apache, just copy apache conf to
``/etc/httpd/conf.d/``.

I presume that the conf file is named nitrate-httpd.conf.

.. literalinclude:: ../../contrib/conf/nitrate-httpd.conf
   :language: bash

Change any configuration to fit your deployment environment.

In ``/etc/httpd/conf/httpd.conf``, set the following settings simply::

    ServerName example.com:80
    Listen ip_address:80

After configuration, run::

    sudo service httpd start

Please go to browser to have a verify if this service runs successfully.

If any problem, please refer to log file::

    /var/log/httpd/error_log

Or any access info, refer to::

    /var/log/httpd/access_log
