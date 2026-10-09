"""Delete the block_api record."""

import logging

from plone.registry.interfaces import IRegistry
from zope.component import getUtility


logger = logging.getLogger(__name__)

RECORD = "plone.blicca.auroraeditor.blockaddons/collective.fragmentsblock.fragment.block_api"


def upgrade(context):
    """Block add-ons are checked by the names their bundles import (ADR 0024): delete the fragment block's orphaned block_api record.

    Upgrade from profile version 1002 to 1003.
    """
    logger.info("Running upgrade step: Delete the block_api record")
    registry = getUtility(IRegistry)
    if RECORD in registry.records:
        del registry.records[RECORD]
