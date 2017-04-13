Installing Nitrate with Apache (virtualenv) and MySQL
=====================================================

.. note::

    The steps in this section have been initially written with
    Red Hat Enterprise Linux 7 in mind. The steps should apply to other
    Linux distributions as well but file locations may vary!

Install Apache and prepare a local Nitrate directory
----------------------------------------------------

First install Apache and mod_wsgi if not present::

    # yum install httpd mod_wsgi
    # systemctl enable httpd
    # systemctl start httpd

Next create a directory that will host your Nitrate instance::

    # mkdir /var/www/html/mynitrate

Prepare virtualenv
------------------

You will install Nitrate inside a virtual environment to avoid conflicts with
system Python libraries and allow for easier upgrade of dependencies::

    # cd /var/www/html/mynitrate
    # yum install python-virtualenv
    # virtualenv venv
    # ./venv/bin/activate


Install Nitrate from source code
--------------------------------

First install RPM packages which are needed to compile some of the Python
dependencies. See :doc:`set_dev_env` for more information. Then::

    (venv)# cd /home/<username>/
    (venv)# git clone https://github.com/Nitrate/Nitrate.git
    (venv)# cd ./Nitrate/
    (venv)# git checkout --track [a proper tag or branch]
    (venv)# pip install -r ./requirements/mysql.txt
    (venv)# python setup.py install

.. note::

    Nitrate source code has been cloned into your home directory but
    has been installed into the virtual environment for Apache!

.. note::

    Alternatively you can use ``requirements/postgres.txt`` for PostgreSQL!


Initialize database
-------------------

Database is required by Nitrate. Django ORM supports many database backends, but
for the moment we recommend you to use MySQL because some parts of Nitrate do not
use the ORM layer but instead hand-crafted SQL queries!
Create database and user for Nitrate in MySQL::

    mysql> create database nitrate;
    mysql> GRANT all privileges on nitrate.* to nitrate@'%' identified by 'password';

Configure Nitrate
-----------------

Create the following files.


``/var/www/html/mynitrate/__init__.py`` - empty

``/var/www/html/mynitrate/settings.py``::

    from tcms.settings.product import *

    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = 'top-secret'
    
    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG = False

    # Database settings
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'nitrate',
            'HOST': '',
            'USER': 'nitrate',
            'PASSWORD': 'password',
        },
    }
    # Nitrate defines a 'slave_1' connection
    DATABASES['slave_1'] = DATABASES['default']
    
    STATIC_ROOT = '/var/www/html/mynitrate/static'


``/var/www/html/mynitrate/wsgi.py``::

    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()


Create tables, create super user and collect static files::

    (venv)# cd /var/www/html/mynitrate
    (venv)# django-admin.py migrate --settings=settings
    (venv)# django-admin.py createsuperuser --settings=settings
    (venv)# django-admin.py collectstatic --settings=settings

Verify that your configuration works by::

    (venv)# django-admin.py runserver --settings=settings

.. note::

    For more information about Nitrate configuration see
    :doc:`configuration`!

Create upload directory
-----------------------

Create upload directory and change owner & group to ``apache``::

    # mkdir -p /var/nitrate/uploads
    # chown apache:apache /var/nitrate/uploads


Configure Apache and mod_wsgi
-----------------------------

``/etc/httpd/conf.d/nitrate.conf``::

    WSGIDaemonProcess nitrateapp python-path=/var/www/html/mynitrate:/var/www/html/mynitrate/venv/lib/python2.7/site-packages
    WSGIProcessGroup nitrateapp
    WSGIScriptAlias / /var/www/html/mynitrate/wsgi.py

    Alias /static/ /var/www/html/mynitrate/static/

    <Location "/static/">
        Options -Indexes
    </Location>

Then restart Apache::

    # systemctl restart httpd


In case of problem, refer to log file::

    /var/log/httpd/error_log

For access info, refer to::

    /var/log/httpd/access_log


Apache and mod_wsgi can be configured in many ways. Another example of
Apache configuration for Nitrate is shown below. You will very likely
have to adjust it based on your particular environment.

.. literalinclude:: ../../contrib/conf/nitrate-httpd.conf
   :language: bash
