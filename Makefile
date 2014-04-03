
TMP = $(CURDIR)/tmp
VERSION = $(shell grep ^Version python-nitrate.spec | sed 's/.* //')

# Push files to the production web only when in the master branch
ifeq "$(shell git rev-parse --abbrev-ref HEAD)" "master"
PUSH_URL = fedorapeople.org:public_html/python-nitrate
else
PUSH_URL = fedorapeople.org:public_html/python-nitrate/testing
endif

PACKAGE = python-nitrate-$(VERSION)
DOCS = $(TMP)/$(PACKAGE)/docs
EXAMPLES = $(TMP)/$(PACKAGE)/examples
CSS = --stylesheet=style.css --link-stylesheet
FILES = COPYING README \
		Makefile python-nitrate.spec \
		docs examples source

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
	# Documentation
	scp $(DOCS)/*.{css,html} $(PUSH_URL)
	# Examples
	scp $(EXAMPLES)/*.py $(PUSH_URL)/examples
	# Archives & rpms
	scp python-nitrate.spec \
		$(TMP)/SRPMS/$(PACKAGE)* \
		$(TMP)/RPMS/noarch/$(PACKAGE)* \
		$(TMP)/SOURCES/$(PACKAGE).tar.bz2 \
		$(PUSH_URL)/download

clean:
	rm -rf $(TMP) source/*.pyc
