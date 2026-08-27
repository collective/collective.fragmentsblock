"""Module where all interfaces, events and exceptions live."""

from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class ICollectiveFragmentsblockLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IFragmentsProvider(Interface):
    """A named utility contributing fragment markup for classic rendering.

    The editor half of a fragment lives in the JS registry (the provider
    add-on's install function registers id/title/html into
    ``@plone/registry``); this is its server-side counterpart, so Blicca
    classic pages render the same file. Register one named utility per
    provider add-on — ``collective.fragmentsblock.fragments.FragmentsFolder``
    is the stock implementation over a package directory.
    """

    def get(fragment_id):
        """Return the fragment's raw HTML (str), or ``None`` if unknown."""
