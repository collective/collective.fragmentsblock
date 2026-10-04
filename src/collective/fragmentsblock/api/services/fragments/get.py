"""The ``@fragments`` service: every registered fragment, for the editor.

The fragment block's install() fetches this before the editor's first
render and registers each item into the JS registry (ADR 0002). The items
are ``fragments.records()`` as they are: the dict is the record both halves
share.
"""

from plone.restapi.services import Service

from collective.fragmentsblock import fragments


class FragmentsGet(Service):
    def reply(self):
        return {
            "@id": f"{self.context.absolute_url()}/@fragments",
            "items": fragments.records(),
        }
