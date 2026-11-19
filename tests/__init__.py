# The project's test package.
#
# An empty ``__init__.py`` makes ``tests`` a *regular* package so that
# ``from tests.known_issues import ...`` (used by conftest.py) always
# resolves to this directory -- even on machines that have a stray
# third-party package named ``tests`` installed in site-packages, which
# would otherwise shadow it.
