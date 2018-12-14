install:
	pipenv install --three

publish: bumpversion
	git push --tags
	pipenv run python setup.py bdist_wheel
	twine upload -r pypi dist/*
	rm -fr build dist .egg switch_inputs.egg-info

.PHONY: bumpversion
bumpversion:
	pipenv run bumpversion minor
