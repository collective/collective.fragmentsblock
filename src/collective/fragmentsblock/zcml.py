"""The ``fragments:folder`` ZCML directive."""

import os.path

from zope.component.zcml import utility
from zope.configuration.exceptions import ConfigurationError
from zope.interface import Interface
from zope.schema import TextLine

from collective.fragmentsblock.fragments import FragmentsFolder
from collective.fragmentsblock.interfaces import IFragmentsProvider


class IFragmentsFolderDirective(Interface):
    directory = TextLine(
        title="Directory",
        description="Folder of <id>.html files, relative to the package.",
        required=True,
    )

    name = TextLine(
        title="Name",
        description="Provider name. Defaults to the package name.",
        required=False,
    )


def fragments_folder(_context, directory, name=None):
    if _context.package is None:
        raise ConfigurationError("fragments:folder must be used inside a package")
    path = _context.path(directory)
    if not os.path.isdir(path):
        raise ConfigurationError(f"fragments:folder directory not found: {path}")
    utility(
        _context,
        provides=IFragmentsProvider,
        component=FragmentsFolder(path),
        name=name or _context.package.__name__,
    )
