"""
Register Controller.

This Page class is generated from a template.
"""

from flet import *
from fletx.core import FletXPage
from fletx.navigation import go_back, navigate

# Import your modules here...
from app.components import Registerform


class RegisterPage(FletXPage):
    """Register Page"""

    def __init__(self):
        super().__init__(
            padding = padding.symmetric(horizontal = 25, vertical = 0),
            bgcolor = Theme.scaffold_bgcolor
        )

        # ...

    def on_init(self):
        """Hook called when RegisterPage in initialized"""

        print("RegisterPage is initialized")

    def on_destroy(self):
        """Hook called when RegisterPage will be unmounted."""

        print("RegisterPage is destroyed")

    def build(self)-> Control:
        """Method that build RegisterPage content"""

        return SafeArea(
            content = Column(
                expand = True,
                alignment = MainAxisAlignment.START,
                horizontal_alignment = CrossAxisAlignment.START,
                controls = [
                    # HEADER
                    IconButton(
                        icon = Icons.ARROW_BACK,
                        icon_color = Colors.ON_SURFACE,
                        on_click = lambda e: go_back(),
                    ),
                    Text(
                        "Join PyTogo Today 🎉",
                        size = 24,
                        weight = FontWeight.BOLD
                    ),
                    Text(
                        "Embark on a shopping journey with us.",
                        size = 14,
                        color = Colors.ON_SURFACE_VARIANT
                    ),

                    # SPACER
                    Container(
                        height = 20
                    ),

                    # FORM
                    Registerform(
                        on_submit = lambda _: None,
                    )
                ]
            )
        )