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

Before starting Kiwi TCMS you need to clone the git repo::

    git clone https://github.com/kiwitcms/Kiwi.git


Then you can start Kiwi TCMS by executing::

    cd Kiwi/
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

    cd Kiwi/
    git pull # to refresh docker-compose.yml
    docker-compose down
    # make docker-image if you build from source or
    docker pull kiwitcms/kiwi # to fetch latest version from Docker Hub
    docker-compose up -d
    docker exec -it kiwi_web /Kiwi/manage.py migrate

.. note::

    Uploads and database data should stay intact because they are split into
    separate volumes which makes upgrading very easy. However you may want to
    back these up before upgrading!


SSL configuration
-----------------

By default Kiwi TCMS is served via HTTPS. ``docker-compose.yml`` is configured with
a default self-signed certificate stored in ``etc/kiwitcms/ssl/``. If you want to
use different SSL certificate you need to update the ``localhost.key`` and
``localhost.crt`` files in that directory or bind-mount your own SSL directory to
``/etc/kiwitcms/ssl`` inside the docker container!

More information about generating your own self-signed certificates can be found at
https://wiki.centos.org/HowTos/Https.


Customization
-------------

You can edit ``docker-compose.yml`` to mount the local file
``local_settings.py`` inside the running Docker container as ``product.py``::

        volumes:
            - uploads:/var/kiwi/uploads
            - ./local_settings.py:/venv/lib64/python3.6/site-packages/tcms/settings/product.py

You can override any default settings in this way!

You can also build your own customized version of Kiwi TCMS by adjusting
the contents of ``Dockerfile`` and then::

    docker build -t my_org/my_kiwi:<version> .

.. note::

    Make sure to modify ``docker-compose.yml`` to use your customized image
    instead the default ``kiwitcms/kiwi:latest``!

.. warning::

    Some older versions of docker do not allow mounting of files between the
    host and the container, they only allow mounting directories and volumes.
    The stock docker versions on CentOS 7 and RHEL 7 do this. You may see an
    error similar to:

    ERROR: for kiwi_web Cannot start service web:
        OCI runtime create failed: container_linux.go:348:
            starting container process caused "process_linux.go:402:
                container init caused "rootfs_linux.go:58: mounting
                    "/root/kiwi/local_settings.py" to
                    rootfs "/var/lib/docker/overlay2 ....

    In this case you will either have to upgrade your docker version
    or `COPY` the desired files and rebuild the docker image!


Troubleshooting
----------------

When started via docker-compose Kiwi TCMS will store the HTTPD logs from the
container in the directory ``log/httpd`` on the host! Errors are usually found
in ``ssl_error_log``.

In case you see a 500 Internal Server Error page and the error log does not
provide a traceback you should configure the ``DEBUG`` setting to ``True`` and
restart the docker container. If your changes are picked up correctly you
should see an error page with detailed information about the error instead of
the default 500 error page.

When reporting issues please copy the relevant traceback as plain text into
your reports!
