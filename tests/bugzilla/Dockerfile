FROM fedora

RUN dnf -y install bugzilla "perl(DBD::SQLite)" findutils
# install optional modules, incl. XMLRPC
RUN /usr/share/bugzilla/checksetup.pl --check-modules 2>/dev/null | grep "dnf install" | cut -f2-99 -d: | sed "s/dnf install//" | xargs dnf -y install
RUN /usr/share/bugzilla/checksetup.pl --check-modules

COPY . /root/
RUN patch -b /usr/share/bugzilla/Bugzilla/Util.pm /root/Util.pm.patch

# generate /etc/bugzilla/localconfig
RUN /usr/share/bugzilla/checksetup.pl /root/checksetup_answers.txt


EXPOSE 80
CMD /usr/sbin/httpd -DFOREGROUND
