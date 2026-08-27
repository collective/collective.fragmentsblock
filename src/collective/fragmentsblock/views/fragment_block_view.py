"""FragmentBlockView browser view.

Server renderer for the Aurora fragment block
"""
from Products.Five.browser import BrowserView


class FragmentBlockView(BrowserView):
    """Server renderer for the Aurora fragment block"""

    def __call__(self):
        return '<li class="heading">FragmentBlockView</li>'
