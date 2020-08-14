default: help

PATH_TO_SITE_PACKAGES = $(shell python -c 'from distutils.sysconfig import get_python_lib; print(get_python_lib())')

FLAKE8_EXCLUDE=.git

.PHONY: flake8
flake8:
	@flake8 --exclude=$(FLAKE8_EXCLUDE) tcms *.py kiwi_lint tcms_settings_dir


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
	./manage.py compilemessages
	if [ "$$TEST_DB" == "all" ]; then \
		for DB in SQLite MySQL Postgres MariaDB; do \
			TEST_DB=$$DB make test; \
		done; \
	else \
		PYTHONWARNINGS=d coverage run --source='.' ./manage.py test -v2 --noinput --settings=$(DJANGO_SETTINGS_MODULE); \
	fi


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
	PYTHONPATH=.:./tcms/ DJANGO_SETTINGS_MODULE=$(DJANGO_SETTINGS_MODULE) pylint --load-plugins=pylint_django.checkers.migrations -d missing-docstring -d duplicate-code --module-naming-style=any  tcms/*/migrations/*
	PYTHONPATH=.:./tcms/ DJANGO_SETTINGS_MODULE=$(DJANGO_SETTINGS_MODULE) pylint --load-plugins=pylint_django --load-plugins=kiwi_lint --load-plugins=pylint.extensions.docparams -d missing-docstring -d duplicate-code tcms/ tcms_settings_dir/

.PHONY: bandit
bandit:
	bandit -r *.py tcms/ kiwi_lint/ tcms_settings_dir/


.PHONY: bandit_site_packages
bandit_site_packages:
	if [ -d "$(PATH_TO_SITE_PACKAGES)" ]; then \
	    bandit -a vuln -r $(PATH_TO_SITE_PACKAGES); \
	fi


.PHONY: docker-image
docker-image:
	sudo rm -rf dist/
	docker build -t kiwitcms/buildroot -f Dockerfile.buildroot .
	docker run --rm --security-opt label=disable \
	            -v `pwd`:/host --entrypoint /bin/cp kiwitcms/buildroot \
	            -r /Kiwi/dist/ /host/
	docker run --rm --security-opt label=disable \
	            -v `pwd`:/host --entrypoint /bin/cp kiwitcms/buildroot \
	            -r /venv /host/dist/
	docker build -t kiwitcms/kiwi:latest .
	docker tag kiwitcms/kiwi:latest quay.io/kiwitcms/kiwi:latest


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

.PHONY: doc8
doc8:
	doc8 docs/source

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

LOCAL_DJANGO_PO=tcms/locale/en/LC_MESSAGES/django.po

.PHONY: messages
messages:
	./manage.py makemessages --locale en --no-obsolete \
	    --ignore "test*.py" --ignore "docs/*" --ignore "kiwi_lint/*" \
	    --ignore "*.egg-info/*" --ignore "*/node_modules/*"
	git checkout tcms/locale/eo_UY/

	for APP_NAME in "github-app" "github-marketplace" "kiwitcms-enterprise" "tenants"; do \
	    echo "---- Trying to merge translations from ../$$APP_NAME"; \
	    if [ -d "../$$APP_NAME" ]; then \
	        REMOTE_DJANGO_PO=`find ../$$APP_NAME -type f -wholename "*/locale/en/LC_MESSAGES/django.po"`; \
	        msgcat --use-first -o $(LOCAL_DJANGO_PO) $(LOCAL_DJANGO_PO) $$REMOTE_DJANGO_PO; \
	    fi; \
	done

	ls tcms/locale/en/LC_MESSAGES/*.po | xargs -n 1 -I @ msgattrib -o @ --no-fuzzy @
