.PHONY: docs
docs:
	mdbook build

.PHONY: venv
venv:
	@virtualenv -p python3.7 venv
	@venv/bin/pip install -e .[dev]

.PHONY: requirements.txt
requirements.txt:
	@pip-compile --no-index --no-emit-trusted-host --generate-hashes --output-file requirements.txt setup.py

.PHONY: test
test:
	@pytest
	@flake8 my_iot tests
	@isort -rc -c my_iot tests

.PHONY: tag
tag:
	@$(eval VERSION = $(shell python setup.py --version))
	@git tag -a '$(VERSION)' -m '$(VERSION)'

.PHONY: publish/tag
publish/tag: tag
	@$(eval VERSION = $(shell python setup.py --version))
	@git push origin '$(VERSION)'

.PHONY: docker
docker:
	@docker build -t eigenein/my-iot .

.PHONY:
publish/docker/latest: docker
	@docker push 'eigenein/my-iot:latest'

.PHONY: publish/docker/tag
publish/docker/tag: docker
	@$(eval VERSION = $(shell python setup.py --version))
	@docker tag 'eigenein/my-iot:latest' 'eigenein/my-iot:$(VERSION)'
	@docker push 'eigenein/my-iot:$(VERSION)'

.PHONY: publish/docker
publish/docker: publish/docker/latest publish/docker/tag

.PHONY: dist
dist:
	@rm -rf dist
	@python setup.py sdist bdist_wheel

.PHONY: publish/dist
publish/dist: dist
	@twine upload --verbose dist/*

# Publish everything, use with caution.
.PHONY: publish
publish: publish/tag publish/dist publish/docker
