"""Tests for the ``fragments:folder`` ZCML directive."""

import pytest
from zope.component import getUtility
from zope.configuration import xmlconfig
from zope.configuration.config import ConfigurationMachine
from zope.configuration.exceptions import ConfigurationError
from zope.configuration.xmlconfig import registerCommonDirectives

from collective.fragmentsblock.fragments import FragmentsFolder
from collective.fragmentsblock.fragments import resolve
from collective.fragmentsblock.interfaces import IFragmentsProvider
from collective.fragmentsblock.testing import INTEGRATION_TESTING


def parse(directive):
    """Parse ``directive`` inside the tests package without executing it."""
    context = ConfigurationMachine()
    registerCommonDirectives(context)
    xmlconfig.string(
        f"""
        <configure
            xmlns="http://namespaces.zope.org/zope"
            xmlns:fragments="http://namespaces.plone.org/fragmentsblock"
            package="collective.fragmentsblock.tests">
          <include package="collective.fragmentsblock" file="meta.zcml" />
          {directive}
        </configure>
        """,
        context=context,
        execute=False,
    )
    return context


def provider_names(context):
    names = []
    for action in context.actions:
        discriminator = action["discriminator"]
        if isinstance(discriminator, tuple) and discriminator[:2] == (
            "utility",
            IFragmentsProvider,
        ):
            names.append(discriminator[2])
    return names


def provider_components(context):
    return [
        action["args"][1]
        for action in context.actions
        if action["args"] and action["args"][0] == "registerUtility"
    ]


class TestFolderDirective:
    def test_registers_under_the_package_name(self):
        context = parse('<fragments:folder directory="fragments" />')
        assert provider_names(context) == ["collective.fragmentsblock.tests"]

    def test_resolves_the_directory_relative_to_the_package(self):
        context = parse('<fragments:folder directory="fragments" />')
        (provider,) = provider_components(context)
        assert isinstance(provider, FragmentsFolder)
        assert provider.directory.parts[-2:] == ("tests", "fragments")

    def test_explicit_name_wins(self):
        context = parse('<fragments:folder directory="fragments" name="brand" />')
        assert provider_names(context) == ["brand"]

    def test_missing_directory_fails_at_configuration_time(self):
        with pytest.raises(ConfigurationError, match="directory not found"):
            parse('<fragments:folder directory="nope" />')


class TestRegisteredFolder:
    """The test layer registers ``tests/fragments`` through the directive."""

    layer = INTEGRATION_TESTING

    def test_provider_is_registered(self, integration):
        provider = getUtility(IFragmentsProvider, name="collective.fragmentsblock.tests")
        assert isinstance(provider, FragmentsFolder)

    def test_fragments_resolve(self, integration):
        assert '<aside class="contact-box">' in resolve("contact-box")
