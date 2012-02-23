
TMP = $(CURDIR)/tmp
VERSION = $(shell grep ^Version python-nitrate.spec | sed 's/.* //')
PUSH_URL = fedorapeople.org:public_html/python-nitrate

PACKAGE = python-nitrate-$(VERSION)
DOCS = $(TMP)/$(PACKAGE)/documentation
CSS = --stylesheet=style.css --link-stylesheet
FILES = COPYING README \
		Makefile python-nitrate.spec \
		documentation examples source

all: push clean

build:
	mkdir -p $(TMP)/{SOURCES,$(PACKAGE)}
	cp -a $(FILES) $(TMP)/$(PACKAGE)
	rst2man README | gzip > $(DOCS)/python-nitrate.1.gz
	rst2html README $(CSS) > $(DOCS)/index.html
	rst2man $(DOCS)/nitrate.rst | gzip > $(DOCS)/nitrate.1.gz
	rst2html $(DOCS)/nitrate.rst $(CSS) > $(DOCS)/nitrate.html

tarball: build
	cd $(TMP) && tar cfj SOURCES/$(PACKAGE).tar.bz2 $(PACKAGE)

rpm: tarball
	rpmbuild --define '_topdir $(TMP)' -bb python-nitrate.spec

srpm: tarball
	rpmbuild --define '_topdir $(TMP)' -bs python-nitrate.spec

packages: rpm srpm

push: packages
	scp python-nitrate.spec \
		$(TMP)/SRPMS/$(PACKAGE)* \
		$(TMP)/RPMS/noarch/$(PACKAGE)* \
		$(TMP)/SOURCES/$(PACKAGE).tar.bz2 \
		$(DOCS)/*.{css,html} \
		$(PUSH_URL)

clean:
	rm -rf $(TMP)
