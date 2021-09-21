SPHINXOPTS    ?=
SPHINXBUILD   ?= poetry run sphinx-build
SOURCEDIR     = ./docs
BUILDDIR      = ./docs/_build

export DJANGO_SETTINGS_MODULE = tests.django.settings

.PHONY: help dev-setup dev-server lock tests tox pre-commit black isort pylint flake8 mypy Makefile


help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo ""
	@echo "Custom commands:"
	@echo "  dev-setup   Install poetry, the virtual environment, and pre-commit hook."
	@echo "  dev-server  Run test django server with manage.py"
	@echo "  lock        Resolve dependencies into the poetry lock-file."
	@echo "  tests       Run tests with pytest-cov."
	@echo "  tox         Run tests with tox."
	@echo "  pre-commit  Run pre-commit hooks on all files."
	@echo "  black       Run black on all files."
	@echo "  isort       Run isort on all files."
	@echo "  pylink      Run pylint on all files under pipeline_views/"
	@echo "  flake8      Run flake8 on all files under pipeline_views/"
	@echo "  mypy        Run mypy on all files under pipeline_views/"

dev-setup:
	@echo "If this fails, you may need to add Poetry's bin-directory to PATH and re-run this script."
	@timeout 3
	@curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python -
	@poetry install
	@poetry run pre-commit install

lock:
	@poetry lock

dev-server:
	@poetry run python manage.py runserver

tests:
	@poetry run pytest -vv -s --cov=pipeline_views tests/

tox:
	@poetry run tox

pre-commit:
	@poetry run pre-commit run --all-files

black:
	@poetry run black .

isort:
	@poetry run isort .

pylint:
	@poetry run pylint pipeline_views/

flake8:
	@poetry run flake8 --max-line-length=120 --extend-ignore=E203,E501 pipeline_views/

mypy:
	@poetry run mypy pipeline_views/

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
