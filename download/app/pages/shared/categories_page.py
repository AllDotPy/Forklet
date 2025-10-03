"""
Categories Controller.

This Page class is generated from a template.
"""

from flet import *
from fletx.core import FletXPage

# Import your modules here...


class CategoriesPage(FletXPage):
    """Categories Page"""

    def __init__(self):
        super().__init__(
            padding = 10,
            bgcolor = Colors.BLACK
        )

        # ...

    def on_init(self):
        """Hook called when CategoriesPage in initialized"""

        print("CategoriesPage is initialized")

    def on_destroy(self):
        """Hook called when CategoriesPage will be unmounted."""

        print("CategoriesPage is destroyed")

    def build(self)-> Control:
        """Method that build CategoriesPage content"""

        return Column(
            expand = True,
            alignment = MainAxisAlignment.CENTER,
            horizontal_alignment = CrossAxisAlignment.CENTER,
            controls = [
                Text("CategoriesPage works!", size=24),
            ]
        )