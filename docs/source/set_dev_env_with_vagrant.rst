Setup development environment with Vagrant
==========================================

Vagrant is a great tool to build and setup development environment in a much
quick way. All you need to do is just to

::

    vagrant up --provider virtualbox

After ``vagrant`` succeeds to setup the virtual machine, you get a complete
environment to develop Nitrate. That is,

* a Python virtual environment creatd at ``$HOME/nitrate-env/`` with all
  necessary dependecies installed.

* database is created and initialized with schema and necessary initial data.
  Database name is ``nitrate``, and you are able to login with
  ``nitrate:nitrate``, for example, in either way of following

  ::

    mysql -unitrate -pnitrate nitrate
    mysql -uroot nitrate

* port forwarding. 8000 is mapped to 8087 in the host.

* source code is mounted at ``/code``. So, that is where to run ``djang-admin``
  or other django specific commands.

Run the development server

::

  django-admin runserver --settings=tcms.settings.devel 0.0.0.0:8000

visit http://127.0.0.1:8087 with your favourite web browser.

Happy hacking.
