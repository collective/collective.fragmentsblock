"""Server renderer for the Aurora fragment block (``@type: fragment``).

Registered as ``@@aurora-block-fragment`` per the block add-on contract
§5.1; ``BlockDispatchMixin.render_block_data`` stamps ``self.data`` before
calling. The block stores only the registered fragment's id (plus an
optional ``variables`` mapping); the markup comes from the provider
add-on's ``IFragmentsProvider`` utility — the same file the editor renders
client-side from the JS registry.
"""

from plone.blicca.auroraeditor.rendering import BaseBlockView

from collective.fragmentsblock import fragments


class FragmentBlockView(BaseBlockView):
    """Render a fragment block: the registered markup, as-is."""

    def __call__(self):
        html = fragments.fragment_html(self.data or {})
        if html is None:
            return '<div class="block-fragment block-fragment-unresolved"></div>'
        return f'<div class="block-fragment">{html}</div>'
