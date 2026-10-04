"""Module where all interfaces, events and exceptions live."""

from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class ICollectiveFragmentsblockLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IFragmentsProvider(Interface):
    """A named utility publishing a set of fragments.

    Both surfaces read it: ``fragments.resolve`` renders one fragment on a
    classic page, the ``@fragments`` service lists them all for the editor.
    ``collective.fragmentsblock.fragments.FragmentsFolder`` is the stock
    implementation over a directory of ``<id>.html`` files; the
    ``fragments:folder`` ZCML directive registers one.
    """

    def get(fragment_id):
        """Return the fragment's raw HTML (str), or ``None`` if unknown.

        ``fragments.resolve`` validates the id against the slug rule before
        calling, so an implementation reached that way never sees a path
        traversal. An implementation that may also be called directly is
        responsible for its own bounds.
        """

    def records():
        """Return every fragment as a ``{"id", "title", "html"}`` dict.

        ``id`` satisfies the slug rule, ``title`` is what editors pick by,
        ``html`` is what ``get(id)`` returns.
        """
