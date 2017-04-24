SPECFILE=nitrate.spec

default: help

DIST_DIR=$(shell pwd)/dist/
DEFINE_OPTS=--define "_sourcedir $(PWD)/dist" --define "_srcrpmdir $(PWD)/dist" --define "_rpmdir $(PWD)/dist"


.PHONY: tarball
tarball:
	@python setup.py sdist


.PHONY: srpm
srpm:
	@rpmbuild $(DEFINE_OPTS) -bs $(SPECFILE)


.PHONY: rpm
rpm:
	@rpmbuild $(DEFINE_OPTS) -ba $(SPECFILE)


.PHONY: build
build:
	python setup.py build


.PHONY: install
install:
	python setup.py install


FLAKE8_EXCLUDE=.git,tcms/settings,*sqls.py,urls.py,wsgi.py,*settings.py,*raw_sql.py,*xml2dict*

.PHONY: flake8
flake8:
	@flake8 --exclude=$(FLAKE8_EXCLUDE) tcms *.py


ifeq ($(strip $(TEST_TARGET)),)
	TEST_TARGET=
else
	TEST_TARGET=$(strip (TEST_TARGET))
endif

.PHONY: test
test:
	@pytest $(TEST_TARGET)


.PHONY: check
check: flake8 test


.PHONY: tags
tags:
	@rm -f .tags
	@ctags -R --languages=Python,CSS,Javascript --python-kinds=-im \
		--exclude=build --exclude=tcms/static/js/lib -f .tags


.PHONY: etags
etags:
	@rm -f TAGS
	@ctags -R -e --languages=Python,CSS,Javascript --python-kinds=-im \
		--exclude=build --exclude=tcms/static/js/lib -f TAGS

ifeq ($(DOCKER_ORG),)
  DOCKER_ORG='nitrate'
endif

NITRATE_VERSION=$(shell cat tcms/__init__.py | grep __version__ | cut -f2 -d"'")

docker-image:
	docker build -t $(DOCKER_ORG)/nitrate:$(NITRATE_VERSION) .

docker-run: docker-image
	docker compose up


.PHONY: help
help:
	@echo 'Usage: make [command]'
	@echo ''
	@echo 'Available commands:'
	@echo ''
	@echo '  rpm              - Create RPM'
	@echo '  srpm             - Create SRPM'
	@echo '  tarball          - Create tarball. Run command: python setup.py sdist'
	@echo '  flake8           - Check Python code style throughout whole source code tree'
	@echo '  test             - Run all tests default. Set TEST_TARGET to run part tests of specific apps'
	@echo '  build            - Run command: python setup.py build'
	@echo '  install          - Run command: python setup.py install'
	@echo '  tags             - Refresh tags for VIM. Default filename is .tags'
	@echo '  etags            - Refresh tags for Emacs. Default filename is TAGS'
	@echo '  help             - Show this help message and exit. Default if no command is given'
