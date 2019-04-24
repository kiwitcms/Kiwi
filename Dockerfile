FROM centos:centos7

RUN rpm -Uhv https://dl.fedoraproject.org/pub/epel/7/x86_64/Packages/e/epel-release-7-11.noarch.rpm && \
    yum -y --setopt=tsflags=nodocs install centos-release-scl && \
    yum -y --setopt=tsflags=nodocs install rh-python36 gcc mariadb-devel mariadb \
    postgresql-devel httpd-devel mod_wsgi mod_ssl gettext && \
    yum -y update --setopt=tsflags=nodocs && \
    yum clean all

# Apache configuration for non-root users
EXPOSE 8080
EXPOSE 8443
COPY ./httpd-foreground /httpd-foreground
CMD /httpd-foreground
RUN sed -i 's/Listen 80/Listen 8080/' /etc/httpd/conf/httpd.conf && \
    sed -i 's/Listen 443/Listen 8443/' /etc/httpd/conf.d/ssl.conf && \
    sed -i 's!ErrorLog "logs/error_log"!ErrorLog "/dev/stderr"!' /etc/httpd/conf/httpd.conf && \
    sed -i 's!CustomLog "logs/access_log"!CustomLog "/dev/stdout"!' /etc/httpd/conf/httpd.conf && \
    sed -i 's!ErrorLog logs/ssl_error_log!ErrorLog "/dev/stderr"!' /etc/httpd/conf.d/ssl.conf && \
    sed -i 's!TransferLog logs/ssl_access_log!TransferLog "/dev/stdout"!' /etc/httpd/conf.d/ssl.conf && \
    sed -i 's!CustomLog logs/ssl_request_log!CustomLog "/dev/stdout"!' /etc/httpd/conf.d/ssl.conf && \
    rm -rf /run/httpd && mkdir /run/httpd && chmod -R a+rwx /run/httpd
COPY ./etc/kiwi-httpd.conf /etc/httpd/conf.d/

# make sure Python 3.6 is enabled by default
ENV PATH /opt/rh/rh-python36/root/usr/bin${PATH:+:${PATH}}
ENV LD_LIBRARY_PATH /opt/rh/rh-python36/root/usr/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
ENV PKG_CONFIG_PATH /opt/rh/rh-python36/root/usr/lib64/pkgconfig${PKG_CONFIG_PATH:+:${PKG_CONFIG_PATH}}
ENV XDG_DATA_DIRS "/opt/rh/rh-python36/root/usr/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"

# Create a virtualenv for the application dependencies
RUN virtualenv /venv

# Set virtualenv environment variables. This is equivalent to running
# source /env/bin/activate. This ensures the application is executed within
# the context of the virtualenv and will have access to its dependencies.
ENV VIRTUAL_ENV /venv
ENV PATH /venv/bin:$PATH

# because we get some errors from other packages which need newer versions
RUN pip install --upgrade pip setuptools

# replace standard mod_wsgi with one compiled for Python 3
RUN pip install --no-cache-dir --upgrade pip mod_wsgi && \
    ln -fs /venv/lib64/python3.6/site-packages/mod_wsgi/server/mod_wsgi-py36.cpython-36m-x86_64-linux-gnu.so \
           /usr/lib64/httpd/modules/mod_wsgi.so

# install the application
COPY ./dist/kiwitcms-*.tar.gz /Kiwi/
RUN pip install --no-cache-dir /Kiwi/kiwitcms-*.tar.gz

# install DB requirements b/c the rest should already be installed
COPY ./requirements/ /Kiwi/requirements/
RUN pip install --no-cache-dir -r /Kiwi/requirements/mariadb.txt
RUN pip install --no-cache-dir -r /Kiwi/requirements/postgres.txt

COPY ./manage.py /Kiwi/
COPY ./etc/kiwitcms/ssl/ /Kiwi/ssl/
RUN sed -i "s/tcms.settings.devel/tcms.settings.product/" /Kiwi/manage.py

# create a mount directory so we can properly set ownership for it
RUN mkdir /Kiwi/uploads

# compile translations
RUN /Kiwi/manage.py compilemessages

# collect static files
RUN /Kiwi/manage.py collectstatic --noinput

# from now on execute as non-root
RUN chown -R 1001 /Kiwi/ /venv/ \
    /etc/pki/tls/certs/localhost.crt /etc/pki/tls/private/localhost.key
USER 1001
