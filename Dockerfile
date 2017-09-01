FROM centos/httpd

RUN yum -y --setopt=tsflags=nodocs install centos-release-scl && \
    yum -y --setopt=tsflags=nodocs install rh-python35 gcc mariadb-devel \
    libxml2-devel libxslt-devel httpd-devel mod_wsgi mod_ssl && \
    yum -y update --setopt=tsflags=nodocs

# static files configuration for Apache
COPY ./contrib/conf/kiwi-httpd.conf /etc/httpd/conf.d/

# configure uploads directory
RUN mkdir -p /var/kiwi/uploads && chown apache:apache /var/kiwi/uploads

# make sure Python 3.5 is enabled by default
ENV PATH /opt/rh/rh-python35/root/usr/bin${PATH:+:${PATH}}
ENV LD_LIBRARY_PATH /opt/rh/rh-python35/root/usr/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
ENV PKG_CONFIG_PATH /opt/rh/rh-python35/root/usr/lib64/pkgconfig${PKG_CONFIG_PATH:+:${PKG_CONFIG_PATH}}
ENV XDG_DATA_DIRS "/opt/rh/rh-python35/root/usr/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"

# Create a virtualenv for the application dependencies
RUN virtualenv /venv

# Set virtualenv environment variables. This is equivalent to running
# source /env/bin/activate. This ensures the application is executed within
# the context of the virtualenv and will have access to its dependencies.
ENV VIRTUAL_ENV /venv
ENV PATH /venv/bin:$PATH


# Install Kiwi TCMS dependencies and replace
# standard mod_wsgi with one compiled for Python 3
RUN pip install --upgrade pip mod_wsgi && \
    ln -fs /venv/lib64/python3.5/site-packages/mod_wsgi/server/mod_wsgi-py35.cpython-35m-x86_64-linux-gnu.so \
           /usr/lib64/httpd/modules/mod_wsgi.so

COPY ./requirements/ /Kiwi/requirements/
RUN pip install -r /Kiwi/requirements/mysql.txt

# now remove -devel RPMs used to build Python dependencies
# and also remove everything else, including YUM, that we don't need
RUN rpm -qa | grep "\-devel" | grep -v python-devel | xargs yum -y remove && \
    yum -y remove gcc cpp centos-release-scl perl-* *-headers pygobject3-base \
           gobject-introspection bind-license iso-codes xml-common && \
    yum clean all
RUN rpm -qa | grep yum | xargs rpm -ev && \
    rpm -qa | grep "^python-" | xargs rpm -ev --nodeps && \
    rpm -ev dbus-python libxml2-python rpm-python pyliblzma pygpgme pyxattr && \
    rm -rf /anaconda-post.log /var/cache/yum /etc/yum* /usr/lib64/python2.7

# Add manage.py
COPY ./manage.py /Kiwi/
RUN sed -i "s/tcms.settings.devel/tcms.settings.product/" /Kiwi/manage.py

# Copy the application code to the virtual environment
COPY ./tcms/ /venv/lib64/python3.5/site-packages/tcms/
RUN find /venv/lib64/python3.5/site-packages/tcms/ -name "*.pyc" -delete

# collect static files
RUN /Kiwi/manage.py collectstatic --noinput
