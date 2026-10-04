"""Declare block-api 1.2 on the fragment block record."""

from plone.registry.interfaces import IRegistry
from zope.component import getUtility


RECORD = "plone.blicca.auroraeditor.blockaddons/collective.fragmentsblock.fragment.block_api"


def upgrade(context):
    """The bundle's install() is awaited from block-api 1.2 on; older hosts must skip it."""
    registry = getUtility(IRegistry)
    if RECORD in registry.records:
        registry[RECORD] = "1.2"
