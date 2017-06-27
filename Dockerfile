FROM centos/httpd

# install virtualenv and libraries needed to build the python dependencies
RUN yum -y --setopt=tsflags=nodocs install python-virtualenv gcc mariadb-devel \
    libxml2-devel libxslt-devel mod_wsgi
# enable when you want to update RPM packages
# this will be used for testing building a Docker image with the
# latest possible versions from CentOS!
RUN yum -y update --setopt=tsflags=nodocs
RUN yum clean all

# static files configuration for Apache
COPY ./contrib/conf/kiwi-httpd.conf /etc/httpd/conf.d/

# configure uploads directory
RUN mkdir -p /var/kiwi/uploads
RUN chown apache:apache /var/kiwi/uploads

# Create a virtualenv for the application dependencies
# Using --system-site-packages b/c Apache configuration
# expects the tcms directory to be there!
RUN virtualenv --system-site-packages /venv

# Set virtualenv environment variables. This is equivalent to running
# source /env/bin/activate. This ensures the application is executed within
# the context of the virtualenv and will have access to its dependencies.
ENV VIRTUAL_ENV /venv
ENV PATH /venv/bin:$PATH


# Install KiwiTestPad dependencies
RUN pip install --upgrade pip
COPY ./requirements/ /Kiwi/requirements/
RUN pip install -r /Kiwi/requirements/mysql.txt

# now remove -devel RPMs used to build Python dependencies
RUN yum -y remove gcc mariadb-devel libxml2-devel libxslt-devel

# remove other -devel RPMs pulled in from base images
RUN rpm -qa | grep "\-devel" | grep -v python-devel | xargs yum -y remove

# remove Perl packages pulled in from base images
RUN yum -y remove perl-*

# remove other binaries and left-overs
RUN yum -y remove openssh* *-headers rsync pygobject3-base gobject-introspection \
    w3m

# final clean up
RUN yum clean all

# remove files and directories we can't with yum and rpm
RUN rm -rf /anaconda-post.log

# Add manage.py
COPY ./manage.py /Kiwi/
RUN sed -i "s/tcms.settings.devel/tcms.settings.product/" /Kiwi/manage.py

# Add application code
COPY ./tcms/ /usr/lib/python2.7/site-packages/tcms/
RUN find /usr/lib/python2.7/site-packages/tcms/ -name "*.pyc" -delete

# collect static files
RUN /Kiwi/manage.py collectstatic --noinput
