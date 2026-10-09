"""Upgrade step 1001 -> 1002: the fragment block record declares block-api 2.0."""

import pytest
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.blicca.auroraeditor import blockaddons


PROFILE = "collective.fragmentsblock:default"
NAME = "collective.fragmentsblock.fragment"
PREFIX = f"plone.blicca.auroraeditor.blockaddons/{NAME}"


class TestUpgrade1002:
    @pytest.fixture(autouse=True)
    def _setup(self, integration):
        self.portal = integration["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.setup_tool = self.portal.portal_setup
        # A site at 1001: the record declares 1.2.
        api.portal.set_registry_record(f"{PREFIX}.block_api", "1.2")
        self.setup_tool.setLastVersionForProfile(PROFILE, "1001")

    def test_declares_block_api_2_0(self):
        self.setup_tool.upgradeProfile(PROFILE, dest="1002")
        assert api.portal.get_registry_record(f"{PREFIX}.block_api") == "2.0"

    def test_the_block_loads_again(self):
        self.setup_tool.upgradeProfile(PROFILE, dest="1002")
        statuses = {s.name: s for s in blockaddons.evaluate(self.portal)}
        assert statuses[NAME].loadable

    def test_leaves_the_rest_of_the_record_alone(self):
        api.portal.set_registry_record(f"{PREFIX}.enabled", False)
        self.setup_tool.upgradeProfile(PROFILE, dest="1002")
        assert api.portal.get_registry_record(f"{PREFIX}.enabled") is False
        assert api.portal.get_registry_record(f"{PREFIX}.bundle") == (
            "++plone++collective.fragmentsblock/fragment-block.js"
        )

    def test_reaches_the_profile_version(self):
        self.setup_tool.upgradeProfile(PROFILE, dest="1002")
        assert self.setup_tool.getLastVersionForProfile(PROFILE) == ("1002",)
