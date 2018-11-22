default: help

FLAKE8_EXCLUDE=.git

.PHONY: flake8
flake8:
	@flake8 --exclude=$(FLAKE8_EXCLUDE) tcms *.py kiwi_lint
	@flake8 --exclude=$(FLAKE8_EXCLUDE) tcms_api


DJANGO_SETTINGS_MODULE="tcms.settings.test"

ifeq ($(TEST_DB),MySQL)
	DJANGO_SETTINGS_MODULE="tcms.settings.test.mariadb"
endif

ifeq ($(TEST_DB),MariaDB)
	DJANGO_SETTINGS_MODULE="tcms.settings.test.mariadb"
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

.PHONY: pylint
pylint:
	pylint -d missing-docstring *.py kiwi_lint/
	PYTHONPATH=. pylint --load-plugins=pylint_django --load-plugins=kiwi_lint -d missing-docstring -d duplicate-code tcms/
	PYTHONPATH=. pylint --load-plugins=kiwi_lint --extension-pkg-whitelist=kerberos tcms_api/

.PHONY: bandit
bandit:
	bandit -r *.py tcms/ tcms_api/ kiwi_lint/


.PHONY: bandit_site_packages
bandit_site_packages:
	if [ -d "/home/travis/virtualenv/python3.6.3/lib/python3.6/site-packages/" ]; then \
	    bandit -a vuln -r /home/travis/virtualenv/python3.6.3/lib/python3.6/site-packages/; \
	fi


.PHONY: docker-image
docker-image:
	find -name "*.pyc" -delete
	docker build -t kiwitcms/kiwi:latest .

.PHONY: test-docker-image
test-docker-image: docker-image
	sudo ./tests/runner.sh

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
	    git diff; \
	    echo "FAIL: unmerged docs changes. Pobably auto-generated!"; \
	    echo "HELP: execute 'make docs' and commit to fix this"; \
	    exit 1; \
	fi

.PHONY: help
help:
	@echo 'Usage: make [command]'
	@echo ''
	@echo 'Available commands:'
	@echo ''
	@echo '  flake8           - Check Python code style throughout whole source code tree'
	@echo '  check            - Run all tests.'
	@echo '  docker-image     - Build Docker image'
	@echo '  help             - Show this help message and exit. Default if no command is given'


# only necessary b/c in Travis we call `make smt`
.PHONY: coverity
coverity:
	@echo 'Everything is handled by the Coverity add-on in Travis'
