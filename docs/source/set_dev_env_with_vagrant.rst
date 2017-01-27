Setup development environment with Vagrant
==========================================

``Vagrantfile`` is provided in project root directory. To setup the
development environment, all you need is just to run

::

    vagrant up --provider virtualbox

After ``vagrant`` succeeds to run the virtual machine, you will get a complete
environment to develop Nitrate,

* a Python virtual environment creatd at ``$HOME/nitrate-env/`` with all
  necessary dependecies installed.

* database is created in MariaDB and name is ``nitrate``. It's empty. Before
  hacking and running development server, remmeber to synchronize database
  from models.

  ::

    ./manage.py migrate

* port forwarding. ``8000`` is mapped to ``8087`` in host.

* source code is mounted at ``/code``.

* Run development server

  ::

    ./manage.py runserver 0.0.0.0:8000

visit http://127.0.0.1:8087 with your favourite web browser.

Happy hacking.
