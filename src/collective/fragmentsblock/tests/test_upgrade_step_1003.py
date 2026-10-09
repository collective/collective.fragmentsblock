"""Upgrade step 1002 -> 1003: delete the fragment block's orphaned block_api record."""

import pytest
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.registry import field
from plone.registry import Record
from plone.registry.interfaces import IRegistry
from zope.component import getUtility


PROFILE = "collective.fragmentsblock:default"
NAME = "collective.fragmentsblock.fragment"
PREFIX = f"plone.blicca.auroraeditor.blockaddons/{NAME}"
RECORD = f"{PREFIX}.block_api"


class TestUpgrade1003:
    @pytest.fixture(autouse=True)
    def _setup(self, integration):
        self.portal = integration["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.setup_tool = self.portal.portal_setup
        self.registry = getUtility(IRegistry)
        self.setup_tool.setLastVersionForProfile(PROFILE, "1002")

    def test_deletes_the_orphan_record(self):
        """A site still holding the retired field loses it."""
        self.registry.records[RECORD] = Record(field.TextLine(title="old"), "2.0")
        self.setup_tool.upgradeProfile(PROFILE, dest="1003")
        assert RECORD not in self.registry.records

    def test_tolerates_a_missing_record(self):
        """A site without the orphan record is untouched."""
        assert RECORD not in self.registry.records
        self.setup_tool.upgradeProfile(PROFILE, dest="1003")
        assert RECORD not in self.registry.records

    def test_leaves_the_rest_of_the_record_alone(self):
        self.registry.records[RECORD] = Record(field.TextLine(title="old"), "2.0")
        self.setup_tool.upgradeProfile(PROFILE, dest="1003")
        assert api.portal.get_registry_record(f"{PREFIX}.enabled") is True
        assert api.portal.get_registry_record(f"{PREFIX}.bundle") == (
            "++plone++collective.fragmentsblock/fragment-block.js"
        )

    def test_reaches_the_profile_version(self):
        self.setup_tool.upgradeProfile(PROFILE, dest="1003")
        assert self.setup_tool.getLastVersionForProfile(PROFILE) == ("1003",)
