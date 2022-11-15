Setting up a local development environment
==========================================

Get source code
---------------

The Kiwi TCMS source code is available at https://github.com/kiwitcms/Kiwi::

    git clone https://github.com/kiwitcms/Kiwi.git
    cd Kiwi/

Install Python 3
----------------

Kiwi TCMS is a Python 3 project! Linux is our preferred environment but
you can work on Kiwi TCMS on Windows as well!

Download & install Python from https://www.python.org/downloads/.
All further instructions assume that you have Python 3 enabled.

.. note::

    At the moment Kiwi TCMS is developed and tested with Python 3.9.
    You can always consult ``Dockerfile`` to find out the exact version which we use!


Setup virtualenv
----------------

Create a virtual environment for Kiwi TCMS::

    $ python3 -m venv ~/kiwi-env
    $ source ~/kiwi-env/bin/activate

On Windows, activating the virtual environment is different::

    > python3 -m venv C:\kiwi-env
    > C:\kiwi-env\Scripts\activate

See https://docs.python.org/3/tutorial/venv.html for more information!


Dependencies
------------

On Linux you have to install packages which are needed to compile some of the
Python dependencies::

    sudo yum install gcc python-devel mariadb-devel libffi-devel npm graphviz

.. note::

    Graphviz is only used to build model diagrams from source code!

Then install the necessary Python packages inside your virtual environment::

    pip install -r requirements/mariadb.txt
    pip install -r requirements/devel.txt


.. note::

    Alternatively you can use ``requirements/postgres.txt`` for PostgreSQL!

The user interface needs several Node.js packages.
`Download & install Node first <https://nodejs.org/en/download/>`_ and then::

    cd tcms/
    ./npm-install

inside the ``Kiwi/`` directory.


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

    ./node_modules/.bin/webpack watch
    ./manage.py runserver

Now, open http://127.0.0.1:8000/ and should be presented with your brand new Kiwi TCMS homepage!
