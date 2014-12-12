Setting up a development environment on Fedora
==============================================

Get source code
---------------

The Nitrate source code is available at: https://github.com/Nitrate/Nitrate

You can get the latest changes with git easily::

    git clone https://github.com/Nitrate/Nitrate.git

Install dependencies
--------------------

Install devel packages that should be installed first::

    sudo yum install gcc python-devel mysql-devel krb5-devel libxml2-devel libxslt-devel

Install dependencies from ``requirements/devel.txt``::

    sudo pip install -r requirements/devel.txt

Initialize database
-------------------

Database is required by Nitrate (and all of Django apps). Django ORM supports
many database backends, we recommend you to use MySQL.

Create database and user for nitrate in mysql::

    mysql> create database nitrate;
    mysql> GRANT all privileges on nitrate.* to nitrate@'%' identified by 'password';

Update settings/devel.py::

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

    django-admin.py syncdb --settings=tcms.settings.devel
    django-admin.py migrate --settings=tcms.settings.devel

Load initial data::
 
    django-admin.py loaddata --settings=tcms.settings.devel

Let's run nitrate
-----------------

You're now ready to start the server::

    python manage.py runserver

Now, open http://127.0.0.1:8000/ and should be presented with your brand new Nitrate homepage!
