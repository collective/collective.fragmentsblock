"""Pytest configuration for collective.fragmentsblock tests."""

from pytest_plone import fixtures_factory

from collective.fragmentsblock.testing import FUNCTIONAL_TESTING
from collective.fragmentsblock.testing import INTEGRATION_TESTING


globals().update(
    fixtures_factory((
        (INTEGRATION_TESTING, "integration"),
        (FUNCTIONAL_TESTING, "functional"),
    ))
)
