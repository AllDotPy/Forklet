"""
Latest Controller.

This Page class is generated from a template.
"""

from flet import *
from fletx.core import FletXPage

# Import your modules here...


class LatestPage(FletXPage):
    """Latest Page"""

    def __init__(self):
        super().__init__(
            padding = 10,
            bgcolor = Colors.BLACK
        )

        # ...

    def on_init(self):
        """Hook called when LatestPage in initialized"""

        print("LatestPage is initialized")

    def on_destroy(self):
        """Hook called when LatestPage will be unmounted."""

        print("LatestPage is destroyed")

    def build(self)-> Control:
        """Method that build LatestPage content"""

        return Column(
            expand = True,
            alignment = MainAxisAlignment.CENTER,
            horizontal_alignment = CrossAxisAlignment.CENTER,
            controls = [
                Text("LatestPage works!", size=24),
            ]
        )