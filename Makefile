init:
	pip install pipenv --upgrade
	pipenv install --dev --skip-lock
test:
	pipenv run py.test tests/test.py
dist:
	python3 setup.py sdist bdist_wheel --universal
	pip uninstall rtbold
	pip install dist/rtbold-0.0.2-py2.py3-none-any.whl
	rm -rf build dist .egg rtbold.egg-info
publish:
	pip install 'twine>=1.5.0'
	python3 setup.py sdist bdist_wheel --universal
	twine upload dist/*.whl
	rm -fr build dist .egg rtbold.egg-info
