develop:
	python setup.py develop

build:
	cake sbuild
	python setup.py build

test:
	python setup.py nosetests
