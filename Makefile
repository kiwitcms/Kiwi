default: help

DIST_DIR=$(shell pwd)/dist/


.PHONY: tarball
tarball:
	@python setup.py sdist


.PHONY: build
build:
	python setup.py build


.PHONY: install
install:
	python setup.py install


FLAKE8_EXCLUDE=.git,*raw_sql.py

.PHONY: flake8
flake8:
	@flake8 --exclude=$(FLAKE8_EXCLUDE) tcms *.py
	@flake8 --exclude=$(FLAKE8_EXCLUDE) --ignore=F405 tcms_api


DJANGO_SETTINGS_MODULE="tcms.settings.test"

ifeq ($(TEST_DB),MySQL)
	DJANGO_SETTINGS_MODULE="tcms.settings.test.mysql"
endif

ifeq ($(TEST_DB),MariaDB)
	DJANGO_SETTINGS_MODULE="tcms.settings.test.mysql"
endif

ifeq ($(TEST_DB),Postgres)
	DJANGO_SETTINGS_MODULE="tcms.settings.test.postgresql"
endif


.PHONY: test
test:
	if [ "$$TEST_DB" == "all" ]; then \
		for DB in SQLite MySQL Postgres MariaDB; do \
			TEST_DB=$$DB make test; \
		done; \
	else \
		PYTHONWARNINGS=d coverage run --source='.' ./manage.py test --noinput --settings=$(DJANGO_SETTINGS_MODULE); \
	fi

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
  DOCKER_ORG='kiwitcms'
endif

ifeq ($(KIWI_VERSION),)
    KIWI_VERSION=$(shell cat tcms/__init__.py | grep __version__ | cut -f2 -d"'")
endif

docker-image:
	docker build -t $(DOCKER_ORG)/kiwi:$(KIWI_VERSION) .
	docker tag $(DOCKER_ORG)/kiwi:$(KIWI_VERSION) $(DOCKER_ORG)/kiwi:latest

run:
	docker-compose up

.PHONY: docs
docs:
	make -C docs/ html

# checks if all of our documentation/source files are under git!
# this is necessary because ReadTheDocs doesn't call `make' but uses
# conf.py and builds the documentation itself! Since we have some
# auto-generated API docs we want to make sure that we didn't forget
# to regenerate them after code changes!
.PHONY: check-docs-source-in-git
check-docs-source-in-git: docs
	git status
	if [ -n "$$(git status --short)" ]; then \
	    echo "FAIL: unmerged docs changes. Pobably auto-generated!"; \
	    echo "HELP: execute make docs && git add && git commit to fix this"; \
	    exit 1; \
	fi


.PHONY: help
help:
	@echo 'Usage: make [command]'
	@echo ''
	@echo 'Available commands:'
	@echo ''
	@echo '  tarball          - Create tarball. Run command: python setup.py sdist'
	@echo '  flake8           - Check Python code style throughout whole source code tree'
	@echo '  test             - Run all tests.'
	@echo '  build            - Run command: python setup.py build'
	@echo '  install          - Run command: python setup.py install'
	@echo '  tags             - Refresh tags for VIM. Default filename is .tags'
	@echo '  etags            - Refresh tags for Emacs. Default filename is TAGS'
	@echo '  help             - Show this help message and exit. Default if no command is given'
