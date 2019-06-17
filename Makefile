default: help

PATH_TO_SITE_PACKAGES = $(shell python -c 'from distutils.sysconfig import get_python_lib; print(get_python_lib())')

FLAKE8_EXCLUDE=.git

.PHONY: flake8
flake8:
	@flake8 --exclude=$(FLAKE8_EXCLUDE) tcms *.py kiwi_lint


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


.PHONY: l10n-test
l10n-test:
	./manage.py compilemessages
	@make test


# test for missing migrations
# https://stackoverflow.com/questions/54177838/
.PHONY: test_for_missing_migrations
test_for_missing_migrations:
	./manage.py migrate --settings=$(DJANGO_SETTINGS_MODULE)
	./manage.py makemigrations --check --settings=$(DJANGO_SETTINGS_MODULE)

.PHONY: check
check: flake8 test

.PHONY: pylint
pylint:
	pylint -d missing-docstring *.py kiwi_lint/
	PYTHONPATH=.:./tcms/ pylint --load-plugins=pylint_django --load-plugins=kiwi_lint -d missing-docstring -d duplicate-code -d class-based-view-required tcms/
	PYTHONPATH=. DJANGO_SETTINGS_MODULE=$(DJANGO_SETTINGS_MODULE) pylint --load-plugins=pylint_django --load-plugins=kiwi_lint -d all -e class-based-view-required tcms/

.PHONY: bandit
bandit:
	bandit -r *.py tcms/ kiwi_lint/


.PHONY: bandit_site_packages
bandit_site_packages:
	if [ -d "$(PATH_TO_SITE_PACKAGES)" ]; then \
	    bandit -a vuln -r $(PATH_TO_SITE_PACKAGES); \
	fi


.PHONY: docker-image
docker-image:
	find -name "*.pyc" -delete
	./tests/check-build
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
	@echo '  build-for-pypi   - Build tarballs and wheels for PyPI'
	@echo '  docker-image     - Build Docker image'
	@echo '  help             - Show this help message and exit. Default if no command is given'


# only necessary b/c in Travis we call `make smt`
.PHONY: coverity
coverity:
	@echo 'Everything is handled by the Coverity add-on in Travis'


.PHONY: build-for-pypi
build-for-pypi:
	./tests/check-build


.PHONY: messages
messages:
	./manage.py makemessages --no-obsolete --ignore "test*.py"
	ls tcms/locale/*/LC_MESSAGES/*.po | xargs -n 1 -I @ msgattrib -o @ --no-fuzzy @
