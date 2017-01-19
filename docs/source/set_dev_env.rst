Setting up a development environment on Fedora
==============================================

Get source code
---------------

The Nitrate source code is available at: https://github.com/Nitrate/Nitrate

You can get the latest changes with git easily::

    git clone https://github.com/Nitrate/Nitrate.git

Setup virtualenv
----------------

Install devel packages::

    sudo yum install gcc python-devel mysql-devel krb5-devel libxml2-devel libxslt-devel

Create a virtual environment for Nitrate::

    virtualenv ~/virtualenvs/nitrate

Install dependencies from ``requirements/devel.txt``::

    . ~/virtualenvs/nitrate/bin/activate
    pip install -r requirements/devel.txt

Initialize database
-------------------

Currently, MySQL is only be supported, either mysql or mariadb is okay for
running Nitrate.

Create database and user::

    mysql -uroot
    create database nitrate character set utf8;
    GRANT all privileges on nitrate.* to nitrate@'%' identified by 'nitrate';

For convenience for development, user, password and database name are already
set in `tcms/settings/devel.py` with default value. Each of them is `nitrate`.

Load database schema and initial data::

    ./manage.py migrate

Let's run nitrate
-----------------

You're now ready to start the server::

    python manage.py runserver

Now, open http://127.0.0.1:8000/ and should be presented with your brand new Nitrate homepage!
