Setting up a local development environment
------------------------------------------

Get source code
~~~~~~~~~~~~~~~

The KiwiTestPad source code is available at: https://github.com/kiwitcms/Kiwi::

    git clone https://github.com/kiwitcms/Kiwi.git

Setup virtualenv
~~~~~~~~~~~~~~~~

Install devel packages which are needed to compile some of the Python dependencies::

    sudo yum install gcc python-devel mysql-devel libxml2-devel libxslt-devel

Create a virtual environment for KiwiTestPad::

    virtualenv ~/virtualenvs/kiwi

Install dependencies for development::

    . ~/virtualenvs/kiwi/bin/activate
    pip install -r requirements/mysql.txt
    pip install -r requirements/devel.txt

.. note::

    Alternatively you can use ``requirements/postgres.txt`` for PostgreSQL!

Initialize database
-------------------

.. note::

    In development mode KiwiTestPad is configured to use SQLite!
    You may want to adjust the database and/or other configuration settings.
    Override them in ``./tcms/settings/devel.py`` if necessary.

.. warning::

    At the moment KiwiTestPad is not 100% portable between database backends!
    We recommend either MySQL or MariaDB for running KiwiTestPad!

Load database schema and initial data::

    ./manage.py migrate

Let's run KiwiTestPad
---------------------

You're now ready to start the server::

    ./manage.py runserver

Now, open http://127.0.0.1:8000/ and should be presented with your brand new KiwiTestPad homepage!
