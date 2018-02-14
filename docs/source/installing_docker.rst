Running Kiwi TCMS as a Docker container
=========================================

In order to run Kiwi TCMS as a production instance you will need
`Docker <https://docs.docker.com/engine/installation/>`_ and
`docker-compose <https://docs.docker.com/compose/install/>`_. Refer to
their documentation about download and installation options.

Pull or Build Docker image
--------------------------

You can download the official Kiwi TCMS Docker image by running::

    docker pull kiwitcms/kiwi

Alternatively you can build an image yourself by running::

    make docker-image

this will create a Docker image with the latest Kiwi TCMS version.
By default the image tag will be ``kiwitcms/kiwi:<version>``.


Start Docker compose
--------------------

You can start using Kiwi TCMS by executing::

    docker-compose up -d


Your Kiwi TCMS instance will be accessible at https://localhost.

The above command will create two containers:

1) A web container based on the latest Kiwi TCMS image
2) A DB container based on the official centos/mariadb image


``docker-compose`` will also create two volumes for persistent data storage:
``kiwi_db_data`` and ``kiwi_uploads``.

.. note::

    Kiwi TCMS container will bind to all network addresses on the system.
    To use it across the organization simply distribute the FQDN of the system
    running the Docker container to all associates.


Initial configuration of running container
------------------------------------------

You need to do initial configuration by executing::

    docker exec -it kiwi_web /Kiwi/manage.py migrate
    docker exec -it kiwi_web /Kiwi/manage.py createsuperuser

This will create the database schema and create the first user in the system!

Upgrading
---------

To upgrade running Kiwi TCMS containers execute the following commands::

    docker-compose down
    # make docker-image if you build from source or
    docker pull kiwitcms/kiwi # to fetch latest version from Docker Hub
    docker-compose up -d
    docker exec -it kiwi_web /Kiwi/manage.py migrate

.. note::

    Uploads and database data should stay intact because they are split into
    separate volumes, which makes upgrading very easy. However you may want to
    back these up before upgrading!


SSL configuration
-----------------

By default Kiwi TCMS is served via HTTPS. This docker compose is configured with
a default self-signed certificate. If you want to use a different SSL certificate
you need to update the ``kiwi-https.key`` and ``kiwi-https.crt`` files! More information
about generating your own self-signed certificates can be found at
https://wiki.centos.org/HowTos/Https.


Customization
-------------

You can edit ``docker-compose.yml`` to mount the local file
``local_settings.py`` inside the running Docker container as ``product.py``::

        volumes:
            - uploads:/var/kiwi/uploads
            - ./local_settings.py:/venv/lib64/python3.5/site-packages/tcms/settings/product.py

You can override any default settings in this way!

You can also build your own customized version of Kiwi TCMS by adjusting
the contents of ``Dockerfile`` and then::

    docker build -t my_org/my_kiwi:<version> .

.. note::

    Make sure to modify ``docker-compose.yml`` to use your customized image
    instead the default ``kiwitcms/kiwi:latest``!
