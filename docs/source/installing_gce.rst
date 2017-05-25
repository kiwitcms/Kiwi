Installing KiwiTestPad with Docker and Google Cloud Engine
==========================================================

It is possible to host KiwiTestPad on Google Cloud Engine as a Docker image.
The image is configured to use Gunicorn as the backend server. To read
more about KiwiTestPad and Gunicorn see :doc:`installing_gunicorn`.

.. warning::

    You need docker running on the local machine and google-cloud-sdk installed
    and configured with proper credentials in order for the commands below to work!


Create Docker image
-------------------

First make sure you are able to start KiwiTestPad via Gunicorn locally!
Then inside your application directory create the following files.

``app.yaml``::

    # Copyright 2015 Google Inc.
    #
    # Licensed under the Apache License, Version 2.0 (the "License");
    # you may not use this file except in compliance with the License.
    # You may obtain a copy of the License at
    #
    #     http://www.apache.org/licenses/LICENSE-2.0
    #
    # Unless required by applicable law or agreed to in writing, software
    # distributed under the License is distributed on an "AS IS" BASIS,
    # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    # See the License for the specific language governing permissions and
    # limitations under the License.
    
    # This file specifies your Python application's runtime configuration.
    # See https://cloud.google.com/appengine/docs/managed-vms/config for details.
    runtime: custom
    vm: true
    entrypoint: custom

Use the following ``Dockerfile`` to build your image::

    # Copyright 2015 Google Inc.
    #
    # Licensed under the Apache License, Version 2.0 (the "License");
    # you may not use this file except in compliance with the License.
    # You may obtain a copy of the License at
    #
    #     http://www.apache.org/licenses/LICENSE-2.0
    #
    # Unless required by applicable law or agreed to in writing, software
    # distributed under the License is distributed on an "AS IS" BASIS,
    # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    # See the License for the specific language governing permissions and
    # limitations under the License
    
    # The Google App Engine python runtime is Debian Jessie with Python installed
    # and various os-level packages to allow installation of popular Python
    # libraries. The source is on github at:
    #   https://github.com/GoogleCloudPlatform/python-docker
    FROM gcr.io/google_appengine/python

    # Create a virtualenv for the application dependencies.
    RUN virtualenv /env

    # Set virtualenv environment variables. This is equivalent to running
    # source /env/bin/activate. This ensures the application is executed within
    # the context of the virtualenv and will have access to its dependencies.
    ENV VIRTUAL_ENV /env
    ENV PATH /env/bin:$PATH

    # update the base OS image
    RUN apt-get update
    RUN apt-get upgrade -y

    # install packages needed to build the Python dependencies
    RUN apt-get install -y libkrb5-dev mysql-client

    RUN pip install -U pip

    # Install gunicorn and KiwiTestPad
    # remove django-s3-folder-storage if you don't use Amazon S3 for static files
    RUN pip install gunicorn django-s3-folder-storage kiwitestpad

    # Add application code.
    ADD . /app

    # Gunicorn is used to run the application on Google App Engine. $PORT is defined
    # by the runtime.
    CMD gunicorn -b :$PORT --keyfile /app/ssl/key.pem --certfile /app/ssl/cert.pem mykiwi.wsgi

.. note::

    ``ssl/`` is a directory containing SSL key and certificate if you'd like to serve
    KiwiTestPad via HTTPS.

.. warning::

    At the time of writing KiwiTestPad is not distributed as a package hosted on
    Python Package Index. The command ``pip install kiwitestpad`` above will fail
    unless you provide it with the exact URL to ``kiwitestpad-X.Y.tar.gz``! You can
    build the package on your own using ``python ./setup.py sdist``!


Build and push the latest version of the image
----------------------------------------------

::

    $ IMAGE="gcr.io/YOUR-ORGANIZATION/kiwi:v$(date +%Y%m%d%H%M)"
    $ docker build --tag $IMAGE .
    $ gcloud docker push $IMAGE


To view all images::

    $ docker images

Create the service for the first time
-------------------------------------

::

    $ kubectl run kiwi --image=gcr.io/YOUR-ORGANIZATION/kiwi:vYYYYMMDDHHMM --port 8080
    $ kubectl expose rc kiwi --port 443 --target-port 8080 --name kiwi-https --type=LoadBalancer

These commands will create a resource controller with a single pod running the
service. After a while you can view the external IP address using the command::

    $ kubectl get svc

Other useful commands (for debugging) are::

    $ kubectl get rc
    $ kubectl get pods


Create DB structure, first user and upload static files
-------------------------------------------------------

The commands below are executed from inside the Docker image
because they need access to ``mykiwi/settings.py``::


    $ kubectl get pods
    NAME            READY     STATUS    RESTARTS   AGE
    kiwi-d2u6p   1/1       Running   0          18h
    
    $ kubectl exec kiwi-d2u6p -i -t -- bash -il
    root@kiwi-d2u6p:/home/vmagent/app# source /env/bin/activate
    (env)root@kiwi-d2u6p:/home/vmagent/app# PYTHONPATH=. django-admin migrate --settings mykiwi.settings
    (env)root@kiwi-d2u6p:/home/vmagent/app# PYTHONPATH=. django-admin createsuperuser --settings mykiwi.settings
    (env)root@kiwi-d2u6p:/home/vmagent/app# PYTHONPATH=. django-admin collectstatic --noinput --settings mykiwi.settings


Updating to new version
-----------------------

* Update KiwiTestPad code and/or settings;
* Create a new Docker image version and upload it to Google Container Engine;
* Update the service to use the latest version of the Docker image::

    $ kubectl rolling-update kiwi --image=gcr.io/YOUR-ORGANIZATION/kiwi:vYYYYMMDDHHMM

where you pass the latest version to the ``--image`` parameter;

* Update static files (see above).

How To Configure
----------------

All configuration needs to go into ``mykiwi/settings.py`` **BEFORE** you build the
Docker image and push it to GCE.

