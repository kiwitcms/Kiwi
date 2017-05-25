Installing KiwiTestPad with Apache (virtualenv) and MySQL
=========================================================

.. note::

    The steps in this section have been initially written with
    Red Hat Enterprise Linux 7 in mind. The steps should apply to other
    Linux distributions as well but file locations may vary!

Install Apache and prepare a local KiwiTestPad directory
---------------------------------------------------------

First install Apache and mod_wsgi if not present::

    # yum install httpd mod_wsgi
    # systemctl enable httpd
    # systemctl start httpd

Next create a directory that will host your KiwiTestPad instance::

    # mkdir /var/www/html/mykiwi

Prepare virtualenv
------------------

You will install KiwiTestPad inside a virtual environment to avoid conflicts with
system Python libraries and allow for easier upgrade of dependencies::

    # cd /var/www/html/mykiwi
    # yum install python-virtualenv
    # virtualenv venv
    # ./venv/bin/activate


Install KiwiTestPad from source code
------------------------------------

First install RPM packages which are needed to compile some of the Python
dependencies. See :doc:`set_dev_env` for more information. Then::

    (venv)# cd /home/<username>/
    (venv)# git clone https://github.com/MrSenko/Kiwi.git
    (venv)# cd ./Kiwi/
    (venv)# git checkout --track [a proper tag or branch]
    (venv)# pip install -r ./requirements/mysql.txt
    (venv)# python setup.py install

.. note::

    KiwiTestPad source code has been cloned into your home directory but
    has been installed into the virtual environment for Apache!

.. note::

    Alternatively you can use ``requirements/postgres.txt`` for PostgreSQL!


Initialize database
-------------------

Database is required by KiwiTestPad. Django ORM supports many database backends, but
for the moment we recommend you to use MySQL because some parts of KiwiTestPad do not
use the ORM layer but instead hand-crafted SQL queries!
Create database and user for KiwiTestPad in MySQL::

    mysql> create database kiwi;
    mysql> GRANT all privileges on kiwi.* to kiwi@'%' identified by 'password';

Configure KiwiTestPad
---------------------

Create the following files.


``/var/www/html/mykiwi/__init__.py`` - empty

``/var/www/html/mykiwi/settings.py``::

    from tcms.settings.product import *

    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = 'top-secret'
    
    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG = False

    # Database settings
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'kiwi',
            'HOST': '',
            'USER': 'kiwi',
            'PASSWORD': 'password',
        },
    }
    # KiwiTestPad defines a 'slave_1' connection
    DATABASES['slave_1'] = DATABASES['default']
    
    STATIC_ROOT = '/var/www/html/mykiwi/static'


``/var/www/html/mykiwi/wsgi.py``::

    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()


Create tables, create super user and collect static files::

    (venv)# cd /var/www/html/mykiwi
    (venv)# django-admin.py migrate --settings=settings
    (venv)# django-admin.py createsuperuser --settings=settings
    (venv)# django-admin.py collectstatic --settings=settings

Verify that your configuration works by::

    (venv)# django-admin.py runserver --settings=settings

.. note::

    For more information about KiwiTestPad configuration see
    :doc:`configuration`!

Create upload directory
-----------------------

Create upload directory and change owner & group to ``apache``::

    # mkdir -p /var/kiwi/uploads
    # chown apache:apache /var/kiwi/uploads


Configure Apache and mod_wsgi
-----------------------------

``/etc/httpd/conf.d/kiwi.conf``::

    WSGIDaemonProcess kiwitestpad python-path=/var/www/html/mykiwi:/var/www/html/mykiwi/venv/lib/python2.7/site-packages
    WSGIProcessGroup kiwitestpad
    WSGIScriptAlias / /var/www/html/mykiwi/wsgi.py

    Alias /static/ /var/www/html/mykiwi/static/

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
Apache configuration for KiwiTestPad is shown below. You will very likely
have to adjust it based on your particular environment.

.. literalinclude:: ../../contrib/conf/kiwi-httpd.conf
   :language: bash
