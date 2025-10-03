"""
Login Controller.

This Page class is generated from a template.
"""

from flet import *
from fletx.core import FletXPage
from fletx.navigation import navigate, go_back

# Import your modules here...
from app.components import Loginform
from app.utils import show_snackbar


class LoginPage(FletXPage):
    """Login Page"""

    def __init__(self):
        super().__init__(
            padding = 25,
            bgcolor = Theme.scaffold_bgcolor
        )

        # ...

    def on_init(self):
        """Hook called when LoginPage in initialized"""

        print("LoginPage is initialized")

    def on_destroy(self):
        """Hook called when LoginPage will be unmounted."""

        print("LoginPage is destroyed")

    def build(self)-> Control:
        """Method that build LoginPage content"""

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
                        "Welcome Back! 👋",
                        size = 24,
                        weight = FontWeight.BOLD
                    ),
                    Text(
                        "Please sign in to access your account.",
                        size = 14,
                        color = Colors.ON_SURFACE_VARIANT
                    ),

                    # SPACER
                    Container(
                        height = 20
                    ),

                    # FORM
                    Loginform(
                        on_submit = lambda _: self.submit(),
                    )
                ]
            )
        )