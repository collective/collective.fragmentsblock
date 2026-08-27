"""Tests for the fragment block server renderer (@@aurora-block-fragment)."""

from pathlib import Path

import pytest
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.blicca.auroraeditor import SOMERSAULT_BLOCK_ID
from plone.blicca.auroraeditor import SOMERSAULT_BLOCK_TYPE
from plone.blicca.auroraeditor.interfaces import IPloneBliccaAuroraeditorLayer
from plone.restapi.behaviors import IBlocks
from zope.component import getGlobalSiteManager
from zope.component import getMultiAdapter
from zope.interface import alsoProvides

from collective.fragmentsblock.fragments import FragmentsFolder
from collective.fragmentsblock.interfaces import ICollectiveFragmentsblockLayer
from collective.fragmentsblock.interfaces import IFragmentsProvider
from collective.fragmentsblock.testing import INTEGRATION_TESTING


def somersault(value):
    return {SOMERSAULT_BLOCK_ID: {"@type": SOMERSAULT_BLOCK_TYPE, "value": value}}


def set_blocks(obj, value):
    alsoProvides(obj, IBlocks)
    obj.blocks = somersault(value)
    obj.blocks_layout = {"items": [SOMERSAULT_BLOCK_ID]}


def fragment_node(fragment_id, variables=None):
    node = {
        "type": "ploneBlock",
        "@type": "fragment",
        "children": [{"text": ""}],
        "fragment": fragment_id,
    }
    if variables is not None:
        node["variables"] = variables
    return node


class TestFragmentBlockRendering:
    """Render pages embedding fragment blocks through the blocks view."""

    layer = INTEGRATION_TESTING

    @pytest.fixture(autouse=True)
    def _setup(self, integration):
        self.portal = integration["portal"]
        self.request = integration["request"]
        alsoProvides(self.request, IPloneBliccaAuroraeditorLayer)
        alsoProvides(self.request, ICollectiveFragmentsblockLayer)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.page = api.content.create(
            container=self.portal, type="Document", id="page", title="A page"
        )
        # a provider add-on's registration, as its ZCML would make it
        gsm = getGlobalSiteManager()
        provider = FragmentsFolder(Path(__file__).parent / "fragments")
        gsm.registerUtility(provider, IFragmentsProvider, name="test.fixture")
        yield
        gsm.unregisterUtility(provider, IFragmentsProvider, name="test.fixture")

    def _render(self, obj):
        view = getMultiAdapter((obj, self.request), name="aurora-blocks-view")
        return view.render()

    def test_view_registered(self):
        view = getMultiAdapter((self.page, self.request), name="aurora-block-fragment")
        assert view is not None

    def test_renders_registered_markup_as_is(self):
        set_blocks(self.page, [fragment_node("contact-box")])
        html = self._render(self.page)
        assert '<div class="block-fragment">' in html
        assert '<aside class="contact-box">' in html
        assert "<h2>Contact</h2>" in html

    def test_variables_substituted_and_escaped(self):
        set_blocks(
            self.page,
            [fragment_node("contact-box", {"phone": "<b>+49 & 30</b>"})],
        )
        html = self._render(self.page)
        assert "&lt;b&gt;+49 &amp; 30&lt;/b&gt;" in html

    def test_missing_variable_renders_empty(self):
        set_blocks(self.page, [fragment_node("contact-box")])
        html = self._render(self.page)
        assert '<p class="contact-box-phone"></p>' in html

    def test_unknown_fragment_renders_placeholder(self):
        set_blocks(self.page, [fragment_node("nope")])
        html = self._render(self.page)
        assert "block-fragment-unresolved" in html

    def test_missing_fragment_key_renders_placeholder(self):
        node = fragment_node("x")
        del node["fragment"]
        set_blocks(self.page, [node])
        html = self._render(self.page)
        assert "block-fragment-unresolved" in html

    def test_traversal_shaped_id_renders_placeholder(self):
        set_blocks(self.page, [fragment_node("../conftest")])
        html = self._render(self.page)
        assert "block-fragment-unresolved" in html
