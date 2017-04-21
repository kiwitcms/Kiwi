Running Nitrate as a Docker container
=====================================

Build Docker image
------------------

You can build a Docker image of Nitrate by running::

    make docker-image

This will create a Docker image based on the official CentOS 7 image
with the latest Nitrate. By default the image tag will be
``nitrate/nitrate:<version>``.


Create Docker container
-----------------------

You can then start using Nitrate by executing::

    docker-compose up -d


This will create two containers:

1) A web container based on the latest Nitrate image
2) A DB container based on the official centos/mariadb image


``docker-compose`` will also create two volumes for persistent data storage:
``nitrate_db_data`` and ``nitrate_uploads``.


Initial configuration of running container
------------------------------------------

You need to do initial configuration by executing::

    docker exec -it nitrate_web_1 /Nitrate/manage.py migrate
    docker exec -it nitrate_web_1 /Nitrate/manage.py createsuperuser

Upgrading
---------

To upgrade running Nitrate containers execute the following commands::

    git pull
    make docker-image
    docker-compose stop
    docker rm nitrate_web_1 nitrate_db_1
    docker-compose up -d
    docker exec -it nitrate_web_1 /Nitrate/manage.py migrate

.. note::
    Uploads and database data should stay intact because they are split into
    separate volumes, which makes upgrading very easy. However you may want to
    back these up before upgrading!
