"""Tests for FragmentBlockView view."""
import pytest
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.component import getMultiAdapter
from zope.interface import alsoProvides
from zope.publisher.browser import TestRequest

from collective.fragmentsblock.interfaces import ICollectiveFragmentsblockLayer
from collective.fragmentsblock.testing import INTEGRATION_TESTING


class TestViewFragmentBlockView:
    """Test FragmentBlockView view."""

    layer = INTEGRATION_TESTING

    def _make_request(self):
        """A request carrying the addon browser layer."""
        request = TestRequest()
        alsoProvides(request, ICollectiveFragmentsblockLayer)
        return request

    @pytest.fixture(autouse=True)
    def _setup(self, integration):
        self.portal = integration["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.context = api.content.create(
            container=self.portal,
            type="Document",
            id="test-document",
            title="Test Document",
        )

    def test_view_registered(self):
        """Test view is registered."""
        request = self._make_request()
        view = getMultiAdapter(
            (self.context, request),
            name="aurora-block-fragment",
        )
        assert view is not None

    def test_view_name(self):
        """Test view __name__."""
        request = self._make_request()
        view = getMultiAdapter(
            (self.context, request),
            name="aurora-block-fragment",
        )
        assert view.__name__ == "aurora-block-fragment"
