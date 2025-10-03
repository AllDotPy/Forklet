"""
Bestsellers Controller.

This Page class is generated from a template.
"""

from flet import *
from fletx.core import FletXPage

# Import your modules here...


class BestsellersPage(FletXPage):
    """Bestsellers Page"""

    def __init__(self):
        super().__init__(
            padding = 10,
            bgcolor = Colors.BLACK
        )

        # ...

    def on_init(self):
        """Hook called when BestsellersPage in initialized"""

        print("BestsellersPage is initialized")

    def on_destroy(self):
        """Hook called when BestsellersPage will be unmounted."""

        print("BestsellersPage is destroyed")

    def build(self)-> Control:
        """Method that build BestsellersPage content"""

        return Column(
            expand = True,
            alignment = MainAxisAlignment.CENTER,
            horizontal_alignment = CrossAxisAlignment.CENTER,
            controls = [
                Text("BestsellersPage works!", size=24),
            ]
        )