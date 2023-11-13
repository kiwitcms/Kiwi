# checkov:skip=CKV_DOCKER_2:Ensure that HEALTHCHECK instructions have been added to container images
FROM fedora:39

RUN dnf -y install httpd && \
    dnf -y install bugzilla "perl(DBD::SQLite)" findutils
# install optional modules, incl. XMLRPC
RUN /usr/share/bugzilla/checksetup.pl --check-modules 2>/dev/null | grep "dnf install" | cut -f2-99 -d: | sed "s/dnf install//" | xargs dnf -y install
RUN /usr/share/bugzilla/checksetup.pl --check-modules

COPY . /root/

# generate /etc/bugzilla/localconfig
RUN /usr/share/bugzilla/checksetup.pl /root/checksetup_answers.txt


EXPOSE 80
CMD /usr/sbin/httpd -DFOREGROUND

RUN sed -i 's!ErrorLog "logs/error_log"!ErrorLog "/dev/stderr"!' /etc/httpd/conf/httpd.conf && \
    sed -i 's!CustomLog "logs/access_log"!CustomLog "/dev/stdout"!' /etc/httpd/conf/httpd.conf && \
    chmod -R a+rwx /run/httpd

# apache
USER 48
