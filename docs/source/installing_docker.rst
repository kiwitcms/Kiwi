Running Kiwi TCMS as a Docker container
=========================================

Build Docker image
------------------

You can build a Docker image of Kiwi TCMS by running::

    make docker-image

This will create a Docker image based on the official CentOS 7 image
with the latest Kiwi TCMS version. By default the image tag will be
``mrsenko/kiwi:<version>``.


Create Docker container
-----------------------

Please see the `kiwi-docker <https://github.com/MrSenko/kiwi-docker>`_
repository for information about running Kiwi TCMS as a Docker container
and doing customizations. The repo allows you to change all Django related
settings in ``product.py`` as well as produce fine-tuned Docker images on your
own.
