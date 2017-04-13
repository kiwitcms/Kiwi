Setting up a development environment on Fedora
==============================================

Get source code
---------------

The Nitrate source code is available at: https://github.com/Nitrate/Nitrate

You can get the latest changes with git easily::

    git clone https://github.com/Nitrate/Nitrate.git

Setup virtualenv
----------------

Install devel packages which are needed to compile some of the Python dependencies::

    sudo yum install gcc python-devel mysql-devel krb5-devel libxml2-devel libxslt-devel

Create a virtual environment for Nitrate::

    virtualenv ~/virtualenvs/nitrate

Install dependencies for development::

    . ~/virtualenvs/nitrate/bin/activate
    pip install -r requirements/mysql.txt
    pip install -r requirements/devel.txt

.. note::

    Alternatively you can use ``requirements/postgres.txt`` for PostgreSQL!

Initialize database
-------------------

Currently we recommend either MySQL or MariaDB for running Nitrate. Support
for PostgreSQL is still experimental.

Create database and user::

    mysql -uroot
    create database nitrate character set utf8;
    GRANT all privileges on nitrate.* to nitrate@'%' identified by 'nitrate';

For convenience for development, user, password and database name are already
set in `tcms/settings/devel.py` with default value. Each of them is `nirrate`.

.. note::

    You may want to adjust the database and/or other configuration settings.
    Override them in ``./tcms/settings/devel.py`` if necessary. While the
    Nitrate team prefers MySQL, sqlite appears to work for development
    and some people have used PostgreSQL with varying success in production!
    At the moment Nitrate is not 100% portable between database backends
    due to some hard-coded SQL statements. If you use something other than MySQL
    some parts of the application may not work correctly!

.. warning::

    Do not commit local development overrides to GitHub!

Load database schema and initial data::

    ./manage.py migrate

Let's run Nitrate
-----------------

You're now ready to start the server::

    ./manage.py runserver

Now, open http://127.0.0.1:8000/ and should be presented with your brand new Nitrate homepage!
