# checkov:skip=CKV_DOCKER_7:Ensure the base image uses a non latest version tag
ARG RUNTIME_BASE=quay.io/centos/centos:stream10
FROM $RUNTIME_BASE AS runtime-base

RUN ln -s /usr/bin/microdnf /usr/bin/dnf 2>/dev/null || echo -n && \
    dnf -y --nodocs install python3.12 mariadb-connector-c libpq \
    nginx-core sscg tar glibc-langpack-en && \
    dnf -y --nodocs update && \
    dnf clean all

ENV PATH=/venv/bin:${PATH} \
    VIRTUAL_ENV=/venv

WORKDIR /Kiwi


FROM runtime-base AS buildroot
RUN dnf -y --nodocs install python3.12-devel gzip make \
    mariadb-connector-c-devel postgresql-devel libjpeg-turbo-devel \
    libffi-devel gcc gettext nodejs24-npm unzip which rust cargo findutils && \
    ln -s /usr/bin/npm-24 /usr/bin/npm && \
    ln -s /usr/bin/node-24 /usr/bin/node

COPY ./requirements/mariadb.pc /usr/lib64/pkgconfig/mariadb.pc
COPY . /Kiwi/

RUN python3.12 -m venv /venv && \
    pip3 install --no-cache-dir --upgrade pip setuptools twine wheel && \
    pip3 install --no-cache-dir -r requirements/mariadb.txt -r requirements/postgres.txt

RUN sed -i "s/tcms.settings.devel/tcms.settings.product/" manage.py

# compile tcms/static/js/bundle.js explicitly
RUN pushd tcms/ && npm install --include=dev && ./node_modules/.bin/webpack && popd

RUN ./tests/check-build && \
    pip3 install --no-cache-dir dist/kiwitcms-*.tar.gz


FROM scratch AS pkg-dist
COPY --from=buildroot /Kiwi/dist/ /


FROM runtime-base AS kiwitcms

HEALTHCHECK CMD curl --fail -k -H "Referer: healthcheck" https://127.0.0.1:8443/accounts/login/

EXPOSE 8080
EXPOSE 8443

COPY ./httpd-foreground /httpd-foreground
CMD /httpd-foreground

ENV LC_ALL=en_US.UTF-8     \
    LANG=en_US.UTF-8       \
    LANGUAGE=en_US.UTF-8

COPY --from=buildroot /venv/ /venv
COPY ./manage.py /Kiwi/

# create directories so we can properly set ownership for them
RUN mkdir -p /Kiwi/ssl /Kiwi/static /Kiwi/uploads /Kiwi/etc/cron.jobs
COPY ./etc/*.conf /Kiwi/etc/
COPY ./etc/cron.jobs/* /Kiwi/etc/cron.jobs/

# generate self-signed SSL certificate
RUN /usr/bin/sscg -v -f \
    --country BG --locality Sofia \
    --organization "Kiwi TCMS" \
    --organizational-unit "Quality Engineering" \
    --ca-file       /Kiwi/static/ca.crt     \
    --cert-file     /Kiwi/ssl/localhost.crt \
    --cert-key-file /Kiwi/ssl/localhost.key

RUN sed -i "s/tcms.settings.devel/tcms.settings.product/" /Kiwi/manage.py && \
    ln -s /Kiwi/ssl/localhost.crt /etc/pki/tls/certs/localhost.crt && \
    ln -s /Kiwi/ssl/localhost.key /etc/pki/tls/private/localhost.key


# collect static files
RUN /Kiwi/manage.py collectstatic --noinput --link

# from now on execute as non-root
RUN chown -R 1001 /Kiwi/ /venv/
USER 1001
