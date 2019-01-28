# Python packaging
build:
	python setup.py sdist

upload: build
	twine upload dist/*.tar.gz

clean:
	rm -rf build/ dist/ *.egg-info *.pyc

test:
	python -m unittest -v tests/*.py
