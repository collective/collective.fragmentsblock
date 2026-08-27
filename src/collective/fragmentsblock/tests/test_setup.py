"""Test collective.fragmentsblock installation."""

import pytest
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID


class TestSetup:
    """Test installation and setup."""

    @pytest.fixture(autouse=True)
    def _setup(self, integration):
        self.portal = integration["portal"]

    def test_addon_installed(self):
        """Test addon is installed."""
        installer = api.addon.get_installer(self.portal)
        assert installer.is_product_installed("collective.fragmentsblock")

    def test_browserlayer(self):
        """Test browserlayer is registered."""
        from plone.browserlayer import utils

        from collective.fragmentsblock.interfaces import ICollectiveFragmentsblockLayer

        assert ICollectiveFragmentsblockLayer in utils.registered_layers()

    def test_blockaddon_record_installed(self):
        """The IAuroraBlockAddon record registers the fragment block."""
        from plone.blicca.auroraeditor.interfaces import IAuroraBlockAddon
        from plone.registry.interfaces import IRegistry
        from zope.component import getUtility

        registry = getUtility(IRegistry)
        records = registry.collectionOfInterface(
            IAuroraBlockAddon,
            prefix="plone.blicca.auroraeditor.blockaddons",
            check=False,
        )
        record = records["collective.fragmentsblock.fragment"]
        assert record.bundle == "++plone++collective.fragmentsblock/fragment-block.js"
        assert record.types == ["fragment"]
        assert record.enabled

    def test_addon_loadable_by_wrapper(self):
        """The wrapper's discovery gates accept the add-on: the committed
        bundle and CSS resolve as ++plone++ resources and the declared
        block_api is compatible with the host."""
        from plone.blicca.auroraeditor import blockaddons

        statuses = {s.name: s for s in blockaddons.evaluate(self.portal)}
        status = statuses["collective.fragmentsblock.fragment"]
        assert status.skip_reason is None
        assert status.loadable
        assert status.bundle_url
        assert status.css_url


class TestUninstall:
    """Test uninstallation."""

    @pytest.fixture(autouse=True)
    def _setup(self, integration):
        self.portal = integration["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.installer = api.addon.get_installer(self.portal)
        self.installer.uninstall_product("collective.fragmentsblock")

    def test_addon_uninstalled(self):
        """Test addon is uninstalled."""
        assert not self.installer.is_product_installed("collective.fragmentsblock")

    def test_blockaddon_record_removed(self):
        """Uninstall removes the block add-on record (lockstep)."""
        from plone.blicca.auroraeditor.interfaces import IAuroraBlockAddon
        from plone.registry.interfaces import IRegistry
        from zope.component import getUtility

        registry = getUtility(IRegistry)
        records = registry.collectionOfInterface(
            IAuroraBlockAddon,
            prefix="plone.blicca.auroraeditor.blockaddons",
            check=False,
        )
        assert "collective.fragmentsblock.fragment" not in records

    def test_browserlayer_removed(self):
        """Uninstall removes the browser layer."""
        from plone.browserlayer import utils

        from collective.fragmentsblock.interfaces import ICollectiveFragmentsblockLayer

        assert ICollectiveFragmentsblockLayer not in utils.registered_layers()
