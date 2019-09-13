Setting up a local development environment
==========================================

Get source code
---------------

The Kiwi TCMS source code is available at https://github.com/kiwitcms/Kiwi::

    git clone https://github.com/kiwitcms/Kiwi.git

Install Python 3
----------------

Kiwi TCMS is a Python 3 project! On CentOS 7 this is available via
`SoftwareCollections.org <https://www.softwarecollections.org/en/scls/rhscl/rh-python35/>`_.
All further instructions assume that you have Python 3 enabled. If you are
using software collections then execute::

    scl enable rh-python36 /bin/bash

If you are using a different Linux distribution then consult its documentation
for more details on how to install and enable Python 3!

.. note::

    At the time of writing Kiwi TCMS has been tested with Python 3.6. You can always consult
    ``Dockerfile`` to find out the latest version which we use!

Setup virtualenv
----------------

Create a virtual environment for Kiwi TCMS::

    virtualenv ~/virtualenvs/kiwi


Dependencies
------------

First install RPM packages which are needed to compile some of the Python
dependencies::

    sudo yum install gcc rh-python36-python-devel mariadb-devel libffi-devel npm graphviz

.. note::

    Graphviz is only used to build model diagrams from source code!

Then install dependencies for development::

    . ~/virtualenvs/kiwi/bin/activate
    pip install -r requirements/mariadb.txt
    pip install -r requirements/devel.txt


.. note::

    Alternatively you can use ``requirements/postgres.txt`` for PostgreSQL!

The user interface needs the `PatternFly <http://www.patternfly.org/>`_ library so::

    cd tcms/
    npm install

inside the project directory.


Initialize database
-------------------

.. note::

    In development mode Kiwi TCMS is configured to use SQLite!
    You may want to adjust the database and/or other configuration settings.
    Override them in ``./tcms/settings/devel.py`` if necessary.

Load database schema and create initial user::

    ./manage.py migrate
    ./manage.py createsuperuser

Let's run Kiwi TCMS
-------------------

You're now ready to start the server::

    ./manage.py runserver

Now, open http://127.0.0.1:8000/ and should be presented with your brand new Kiwi TCMS homepage!
