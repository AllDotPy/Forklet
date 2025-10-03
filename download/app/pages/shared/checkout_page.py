"""
Checkout Controller.

This Page class is generated from a template.
"""

from flet import *
from typing import Optional
import flet_webview as ftwv
from fletx.core import FletXPage
from fletx.navigation import go_back, navigate
from fletx.utils import run_async

# Import your modules here...
from app.models import OrderInfo
from app.utils import show_snackbar


class CheckoutPage(FletXPage):
    """Checkout Page"""

    def __init__(self):
        super().__init__(
            padding = padding.symmetric(
                horizontal = 0,
                vertical = 0,
            ),
            bgcolor = Theme.scaffold_bgcolor
        )

        # ...
        self.order: Optional[OrderInfo] = None

    def on_init(self):
        """Hook called when CheckoutPage in initialized"""

        print("CheckoutPage is initialized")

    def on_destroy(self):
        """Hook called when CheckoutPage will be unmounted."""

        print("CheckoutPage is destroyed")

    async def open_dialog(self):
        """Open A given Content in a dialog Box."""

        import asyncio
        await asyncio.sleep(10)

        # Dialog Content
        content = Column(
            # expand = True,
            height = 320,
            spacing = 10,
            alignment = MainAxisAlignment.CENTER,
            horizontal_alignment = CrossAxisAlignment.CENTER,
            controls = [
                Image(
                    src = 'tada.png',
                    width = 130,
                    height = 130,
                    fit = ImageFit.FILL
                ),

                # TITLE
                Text(
                    f"🎉 Payment Successful!",
                    size = 18,
                    weight = FontWeight.BOLD
                ),
                # Text
                Text(
                    f"You have Successful paid {self.order.total} FCFA!.",
                    size = 14,
                ),

                Container(),

                # VIEW ORDER
                FilledButton(
                    width = self.width,
                    height = 50,
                    bgcolor = Colors.PRIMARY,
                    # style = ButtonStyle(
                    # ),
                    content = Row(
                        alignment = MainAxisAlignment.CENTER,
                        controls = [
                            Text(
                                f'View Order',
                                size = 16,
                                color = Colors.ON_PRIMARY,
                                weight = FontWeight.W_500
                            ),
                            Icon(
                                Icons.ARROW_FORWARD,
                                color = Colors.ON_PRIMARY
                            ),
                        ]
                    ),
                    on_click = lambda _: navigate(
                        '/order-details',
                        data = {
                            'order': self.order
                        }
                    ),
                ),

                # RETURN HOME
                FilledButton(
                    width = self.width,
                    height = 50,
                    bgcolor = Colors.SECONDARY,
                    # style = ButtonStyle(
                    # ),
                    content = Row(
                        alignment = MainAxisAlignment.CENTER,
                        controls = [
                            Text(
                                f'Return Home',
                                size = 16,
                                color = Colors.ON_PRIMARY,
                                weight = FontWeight.W_500
                            ),
                            Icon(
                                Icons.ARROW_FORWARD,
                                color = Colors.ON_PRIMARY
                            ),
                        ]
                    ),
                    on_click = lambda _: go_back(),
                ),
            ]
        )

        dlg = AlertDialog(
            # title = Text("Hello"),
            # modal = True,
            content_padding = 10,
            content = content,
            alignment = alignment.center,
            on_dismiss = lambda e: go_back(),
            title_padding = padding.all(0),
        )

        self.page_instance.open(dlg)

    def build(self)-> Control:
        """Method that build CheckoutPage content"""

        # Get Order from navigation
        self.order = self.route_info.data.get('order',None)

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
                                f"Checkout {self.order.total} FCFA",
                                size = 16,
                                weight = FontWeight.W_500
                            ),
                            
                            # PLACE HOLDER
                            Container(
                                width = 40
                            )
                        ]
                    ),
                    ftwv.WebView(
                        url = f"{self.order.transaction.payment_link}",
                        on_page_started = lambda _: run_async(self.open_dialog),
                        on_page_ended = lambda _: print("Page ended"),
                        on_web_resource_error = lambda e: print("Page error:", e.data),
                        expand = True,
                        enable_javascript = True,
                    )
                ]
            )
        )