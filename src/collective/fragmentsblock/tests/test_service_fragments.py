"""The ``@fragments`` service, as the editor fetches it (ADR 0002)."""

import pytest
import requests
import transaction

from collective.fragmentsblock.testing import ACCEPTANCE_TESTING


class TestFragmentsService:
    """Over HTTP, anonymously: the registration, the permission and the JSON shape."""

    layer = ACCEPTANCE_TESTING

    @pytest.fixture(autouse=True)
    def _setup(self, acceptance):
        self.portal = acceptance["portal"]
        self.portal_url = self.portal.absolute_url()
        transaction.commit()
        self.api_session = requests.Session()
        self.api_session.headers.update({"Accept": "application/json"})
        yield
        self.api_session.close()

    def get(self, path):
        return self.api_session.get(f"{self.portal_url}{path}", timeout=30)

    def test_lists_every_registered_fragment(self):
        response = self.get("/@fragments")
        assert response.status_code == 200
        body = response.json()
        assert body["@id"] == f"{self.portal_url}/@fragments"
        assert [item["id"] for item in body["items"]] == ["contact-box", "seal"]

    def test_items_are_the_shared_record_shape(self):
        (contact_box, seal) = self.get("/@fragments").json()["items"]
        assert set(contact_box) == {"id", "title", "html"}
        assert contact_box["title"] == "Contact box"
        assert '<aside class="contact-box">' in contact_box["html"]
        assert seal["title"] == "Seal of approval"
        assert seal["html"].startswith("<!-- title: Seal of approval -->")

    def test_readable_without_logging_in(self):
        # Fragments are trusted markup that public pages already render;
        # the editor fetches with the session cookie, which carries no
        # Bearer token.
        assert self.get("/@fragments").status_code == 200
