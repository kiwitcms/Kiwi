Installing KiwiTestPad with Gunicorn
====================================

Installation
------------

Start by creating a virtualenv for your KiwiTestPad instance::

    $ mkvirtualenv myKiwi

Install Gunicorn::

    (myKiwi)$ pip install gunicorn

Install KiwiTestPad::

    (myKiwi)$ cd ~/path/to/Kiwi
    (myKiwi)$ python ./setup.py install


Configuration
--------------

You need to create a directory holding customized settings to your KiwiTestPad
instance and a ``wsgi.py`` file for Gunicorn::

    (myKiwi)$ mkdir mykiwi

The ``mykiwi/`` directory needs to contain the following files::

    (myKiwi)$ ls -l mykiwi/
    total 0
    -rw-rw-r--. 1 atodorov atodorov    0 Jan 26 11:41 __init__.py
    -rw-rw-r--. 1 atodorov atodorov 1300 Jan 26 11:41 settings.py
    -rw-rw-r--. 1 atodorov atodorov  170 Jan 26 11:41 wsgi.py

``__init__.py`` must be empty. The other files should look like shown below.

``mykiwi/wsgi.py``::

    import os
    
    from django.core.wsgi import get_wsgi_application
    
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mykiwi.settings")
    
    application = get_wsgi_application()


``mykiwi/settings.py``::

    from tcms.settings.product import *
    
    
    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = 'top-secret'
    
    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG = False
    
    # Database settings
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'changeMe',
            'HOST': 'changeMe',
            'USER': 'changeMe',
            'PASSWORD': 'changeMe',
        },
    }

Static files storage with Amazon S3
-----------------------------------

You will also have to configure static files storage for all images, CSS and
JavaScript content. Static files need not be served by Gunicorn directly.
If you want to have Nginx serve them take a look at
http://honza.ca/2011/05/deploying-django-with-nginx-and-gunicorn.

Another very easy and cheap way to host your static files is to
use Amazon S3. If you decide to do this then::

    (myKiwi)$ pip install django-s3-folder-storage

and add the following configuration to `mykiwi/settings.py`::

    INSTALLED_APPS += (
        's3_folder_storage',
    )
    
    # static files storage
    AWS_S3_ACCESS_KEY_ID = "changeMe"
    AWS_S3_SECRET_ACCESS_KEY = "changeMe"
    AWS_STORAGE_BUCKET_NAME = "changeMe"
    
    STATICFILES_STORAGE = 's3_folder_storage.s3.StaticStorage'
    STATIC_S3_PATH = "static"
    STATIC_URL = '//s3.amazonaws.com/%s/%s/' % (AWS_STORAGE_BUCKET_NAME, STATIC_S3_PATH)

.. warning::

    Amazon S3 Frankfurt supports only Sigv4 requests so you need to properly
    instruct the storages layer to handle them. To work around this create
    a file named ``mykiwi/storage.py`` with the following content::

        import os
        from s3_folder_storage.s3 import StaticStorage
        
        os.environ['S3_USE_SIGV4'] = 'True'
        class SigV4Storage(StaticStorage):
            @property
            def connection(self):
                if self._connection is None:
                    self._connection = self.connection_class(
                        self.access_key, self.secret_key,
                        calling_format=self.calling_format, host='s3.eu-central-1.amazonaws.com')
                return self._connection

    then update your ``mykiwi/settings.py``::

        STATICFILES_STORAGE = 'mykiwi.storage.SigV4Storage'
        STATIC_URL = '//s3-eu-central-1.amazonaws.com/%s/%s/' % (AWS_STORAGE_BUCKET_NAME, STATIC_S3_PATH)

After static files storage has been configured execute::

    (myKiwi)$ PYTHONPATH=. django-admin collectstatic --settings mykiwi.settings


Serve KiwiTestPad with Gunicorn
--------------------------------

Once your local KiwiTestPad instance has been configured then create the database::

    (myKiwi)$ PYTHONPATH=. django-admin migrate --settings mykiwi.settings

Then create the first user account on your KiwiTestPad instance::

    (myKiwi)$ PYTHONPATH=. django-admin createsuperuser --settings mykiwi.settings
    Username (leave blank to use 'atodorov'): 
    Email address: atodorov@MrSenko.com
    Password: 
    Password (again): 
    Superuser created successfully.

Afterwards start Gunicorn::

    (myKiwi)$ gunicorn mykiwi.wsgi
    [2017-01-26 11:52:57 +0000] [24161] [INFO] Starting gunicorn 19.6.0
    [2017-01-26 11:52:57 +0000] [24161] [INFO] Listening at: http://127.0.0.1:8000 (24161)
    [2017-01-26 11:52:57 +0000] [24161] [INFO] Using worker: sync
    [2017-01-26 11:52:57 +0000] [24166] [INFO] Booting worker with pid: 24166

Deployment to production
------------------------

Gunicorn advises to use Nginx as an HTTP proxy sitting at the front. For more details
refer to http://gunicorn.org/#deployment.
