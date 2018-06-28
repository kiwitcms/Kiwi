FROM centos/httpd

RUN rpm -Uhv https://dl.fedoraproject.org/pub/epel/7/x86_64/Packages/e/epel-release-7-11.noarch.rpm && \
    yum -y --setopt=tsflags=nodocs install centos-release-scl && \
    yum -y --setopt=tsflags=nodocs install rh-python36 gcc mariadb-devel \
    libxml2-devel libxslt-devel httpd-devel mod_wsgi mod_ssl npm gettext && \
    yum -y update --setopt=tsflags=nodocs && \
    yum clean all

# static configuration for Apache
COPY ./etc/kiwi-httpd.conf /etc/httpd/conf.d/

# configure uploads directory
RUN mkdir -p /var/kiwi/uploads && chown apache:apache /var/kiwi/uploads

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


# Install Kiwi TCMS dependencies and replace
# standard mod_wsgi with one compiled for Python 3
RUN pip install --upgrade pip mod_wsgi && \
    ln -fs /venv/lib64/python3.6/site-packages/mod_wsgi/server/mod_wsgi-py36.cpython-36m-x86_64-linux-gnu.so \
           /usr/lib64/httpd/modules/mod_wsgi.so

COPY ./requirements/ /Kiwi/requirements/
RUN pip install -r /Kiwi/requirements/mysql.txt

# Add manage.py
COPY ./manage.py /Kiwi/
RUN sed -i "s/tcms.settings.devel/tcms.settings.product/" /Kiwi/manage.py

# install patternfly
COPY package.json /Kiwi/
RUN cd /Kiwi/ && npm install && \
    find ./node_modules -type f -not -path "*/dist/*" -delete && \
    find ./node_modules -type d -empty -delete

# Copy the application code to the virtual environment
COPY ./tcms/ /venv/lib64/python3.6/site-packages/tcms/

# compile translations
RUN /Kiwi/manage.py compilemessages

# collect static files
RUN /Kiwi/manage.py collectstatic --noinput
