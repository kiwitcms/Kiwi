FROM registry.access.redhat.com/ubi9-minimal

RUN microdnf -y --nodocs install python3 mariadb-connector-c libpq \
    nginx-core sscg tar glibc-langpack-en && \
    microdnf -y --nodocs update && \
    microdnf clean all

EXPOSE 8080
EXPOSE 8443
COPY ./httpd-foreground /httpd-foreground
CMD /httpd-foreground

ENV PATH=/venv/bin:${PATH} \
    VIRTUAL_ENV=/venv      \
    LC_ALL=en_US.UTF-8     \
    LANG=en_US.UTF-8       \
    LANGUAGE=en_US.UTF-8

# copy virtualenv dir which has been built inside the kiwitcms/buildroot container
# this helps keep -devel dependencies outside of this image
COPY ./dist/venv/ /venv

COPY ./manage.py /Kiwi/
# create directories so we can properly set ownership for them
RUN mkdir /Kiwi/ssl /Kiwi/static /Kiwi/uploads /Kiwi/etc
COPY ./etc/nginx.conf /Kiwi/etc/

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
