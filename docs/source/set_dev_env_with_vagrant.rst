Setup development environment with Vagrant
==========================================

``Vagrantfile.example`` is provided in ``contrib`` directory. To setup the
development environment, copy it to project root directory and name it
``Vagrant``, then run command::

    vagrant up --provider virtualbox

After ``vagrant`` succeeds to run the virtual machine, you will get a complete
environment to develop Nitrate,

* a Python virtual environment creatd at ``$HOME/nitrate-env/`` with all
  necessary dependencies installed.

* a superuser is created by default with username ``admin`` and password
  ``admin``. It is free for you to modify user's properties from Django admin
  WebUI.

* source code is mounted at ``/code``.

* database is created in MariaDB and name is ``nitrate``. It's empty. Before
  hacking and running development server, remember to synchronize database
  from models from ``/code``.

  ::

    ./manage.py migrate

* port forwarding. ``8000`` is mapped to ``8087`` in host.

* Run development server from ``/code``

  ::

    ./manage.py runserver 0.0.0.0:8000

visit http://127.0.0.1:8087 with your favourite web browser.

Happy hacking.
