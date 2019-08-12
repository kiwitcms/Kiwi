# install the node modules first
FROM node:lts-alpine AS nodebuild

COPY ./tcms/package.json ./tcms/package-lock.json /app/

WORKDIR /app

RUN npm install
RUN find ./node_modules -type f -exec touch {} +

# then build the kiwi app
FROM python:3.6-alpine AS pybuild

COPY ./requirements/  /app/requirements/
COPY ./tcms/ /app/tcms/
COPY ./setup.cfg ./*.py ./README.rst ./MANIFEST.in /app/
COPY --from=nodebuild /app/node_modules/ /app/tcms/node_modules/
WORKDIR /app

RUN python setup.py sdist
RUN pip install --no-cache-dir --upgrade pip virtualenv
RUN virtualenv -q /venv

ENV VIRTUAL_ENV=/venv/
ENV PATH=/venv/bin:$PATH

RUN apk add build-base libffi-dev libressl-dev mariadb-dev postgresql-dev
RUN pip install --no-cache-dir -r /app/requirements/mariadb.txt
RUN pip install --no-cache-dir -r /app/requirements/postgresql.txt
RUN pip install --no-cache-dir gunicorn
RUN pip install --no-cache-dir -f dist/ kiwitcms

# tie it all together by serving from nginx
FROM python:3.6-alpine AS server

COPY --from=pybuild /venv/ /venv/

ENV VIRTUAL_ENV=/venv/
ENV PATH=/venv/bin:$PATH

RUN apk add libffi libressl nginx gettext mariadb-connector-c libpq
RUN mkdir -p /Kiwi/uploads /run/kiwi /run/nginx

COPY ./manage.py /Kiwi/
COPY ./requirements/ /Kiwi/requirements/
COPY ./etc/kiwitcms/ssl/ /Kiwi/ssl/
COPY ./etc/kiwi-nginx.conf /etc/nginx/conf.d/default.conf

RUN sed -i 's/tcms.settings.devel/tcms.settings.product/' /Kiwi/manage.py
RUN /Kiwi/manage.py compilemessages
RUN /Kiwi/manage.py collectstatic --noinput

RUN chown -R nginx /Kiwi /run/nginx /run/kiwi
EXPOSE 8080
EXPOSE 8443
ENV GUNICORN_CMD_ARGS="--workers 5 --bind unix:/run/kiwi/kiwi.sock --name kiwi --user nginx --access-logfile - --error-logfile -"
CMD nginx && gunicorn tcms.wsgi