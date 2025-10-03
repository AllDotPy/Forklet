"""
Notifications Controller.

This Page class is generated from a template.
"""

from flet import *
from fletx.core import FletXPage
from fletx.navigation import go_back

# Import your modules here...


class NotificationsPage(FletXPage):
    """Notifications Page"""

    def __init__(self):
        super().__init__(
            padding = padding.symmetric(
                horizontal = 10,
                vertical = 0,
            ),
            bgcolor = Theme.scaffold_bgcolor,
        )

        # ...

    def on_init(self):
        """Hook called when NotificationsPage in initialized"""

        print("NotificationsPage is initialized")

    def on_destroy(self):
        """Hook called when NotificationsPage will be unmounted."""

        print("NotificationsPage is destroyed")

    def build(self)-> Control:
        """Method that build NotificationsPage content"""

        return SafeArea(
            expand = True,
            minimum_padding = 0,
            maintain_bottom_view_padding = False,
            content = Column(
                expand = True,
                alignment = MainAxisAlignment.START,
                horizontal_alignment = CrossAxisAlignment.CENTER,
                controls = [
                    # HEADER
                    Row(
                        width = self.width,
                        height = 60,
                        alignment = MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment = CrossAxisAlignment.CENTER,
                        controls = [
                            IconButton(
                                icon = Icons.ARROW_BACK,
                                icon_color = Colors.ON_SURFACE,
                                on_click = lambda _: go_back()
                            ),

                            # TITLE
                            Text(
                                f"Notifications",
                                size = 16,
                                weight = FontWeight.W_500
                            ),
                            
                            # 
                            Container()
                        ]
                    ),

                    Text("NotificationsPage works!", size=24),
                ]
            )
        )