"""Testing setup for collective.fragmentsblock.

Mirrors the plone.blicca.auroraeditor fixture: plone.volto's ZCML is loaded
(the volto.* metadata behaviors and serializer utilities, as z3c.autoinclude
would in a real site) but its GS profile is never applied — Document stays
non-folderish, Folder stays enabled.
"""

import os

import plone.blicca.auroraeditor
import plone.restapi
import plone.volto
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.testing.zope import WSGI_SERVER_FIXTURE

import collective.fragmentsblock


class CollectiveFragmentsblockLayer(PloneSandboxLayer):
    """Custom testing layer for collective.fragmentsblock."""

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        """Set up Zope."""
        # Compile .po -> .mo so add-on translations load during tests.
        os.environ.setdefault("zope_i18n_compile_mo_files", "true")
        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=plone.volto)
        self.loadZCML(package=plone.blicca.auroraeditor)
        self.loadZCML(package=collective.fragmentsblock)

    def setUpPloneSite(self, portal):
        """Set up Plone site."""
        self.applyProfile(portal, "plone.restapi:default")
        self.applyProfile(portal, "plone.blicca.auroraeditor:default")
        self.applyProfile(portal, "collective.fragmentsblock:default")


FIXTURE = CollectiveFragmentsblockLayer()

INTEGRATION_TESTING = IntegrationTesting(
    bases=(FIXTURE,),
    name="CollectiveFragmentsblockLayer:IntegrationTesting",
)

FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(FIXTURE,),
    name="CollectiveFragmentsblockLayer:FunctionalTesting",
)

ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(FIXTURE, WSGI_SERVER_FIXTURE),
    name="CollectiveFragmentsblockLayer:AcceptanceTesting",
)


# Test credentials
TEST_USER_ID = "testuser"
TEST_USER_NAME = "testuser"
SITE_OWNER_NAME = SITE_OWNER_NAME
SITE_OWNER_PASSWORD = SITE_OWNER_PASSWORD
