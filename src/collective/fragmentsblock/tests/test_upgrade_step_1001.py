"""Upgrade step 1000 -> 1001: the fragment block record declares block-api 1.2."""

import pytest
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

from collective.fragmentsblock.upgrades.v1001 import RECORD
from collective.fragmentsblock.upgrades.v1001 import upgrade


PROFILE = "collective.fragmentsblock:default"


class TestUpgrade1001:
    @pytest.fixture(autouse=True)
    def _setup(self, integration):
        self.portal = integration["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.setup_tool = self.portal.portal_setup
        # A site installed when the record declared 1.0.
        api.portal.set_registry_record(RECORD, "1.0")
        self.setup_tool.setLastVersionForProfile(PROFILE, "1000")

    def test_declares_block_api_1_2(self):
        self.setup_tool.upgradeProfile(PROFILE, dest="1001")
        assert api.portal.get_registry_record(RECORD) == "1.2"

    def test_leaves_the_rest_of_the_record_alone(self):
        self.setup_tool.upgradeProfile(PROFILE, dest="1001")
        prefix = RECORD.rsplit(".", 1)[0]
        assert api.portal.get_registry_record(f"{prefix}.bundle") == (
            "++plone++collective.fragmentsblock/fragment-block.js"
        )
        assert api.portal.get_registry_record(f"{prefix}.enabled") is True

    def test_reaches_the_profile_version(self):
        self.setup_tool.upgradeProfile(PROFILE, dest="1001")
        assert self.setup_tool.getLastVersionForProfile(PROFILE) == ("1001",)

    def test_tolerates_a_missing_record(self):
        registry = getUtility(IRegistry)
        del registry.records[RECORD]
        upgrade(self.setup_tool)
        assert RECORD not in registry.records
