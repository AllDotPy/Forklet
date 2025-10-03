"""
Orderdetails Controller.

This Page class is generated from a template.
"""

from flet import *
from typing import Optional
from fletx.core import FletXPage, RxList
from fletx.navigation import go_back

# Import your modules here...
from app.models import OrderInfo, CartItem
from app.components import (
    CartItemlist, Cartitem,
    Stepper, StepState, Step,
    StepperOrientation
)


class OrderDetailsPage(FletXPage):
    """Orderdetails Page"""

    def __init__(self):
        super().__init__(
            padding = padding.symmetric(
                horizontal = 10,
                vertical = 0,
            ),
            bgcolor = Theme.scaffold_bgcolor
        )

        # ...
        self.order: Optional[OrderInfo] = None

    def on_init(self):
        """Hook called when OrderdetailsPage in initialized"""

        print("OrderdetailsPage is initialized")

    def on_destroy(self):
        """Hook called when OrderdetailsPage will be unmounted."""

        print("OrderdetailsPage is destroyed")

    def build_stepper(self):
        """Build Order Stepper"""

        steps = [
            Step(
                title = "Payment",
                icon = Icons.PAYMENT,
                state = StepState.COMPLETED
            ),
            Step(
                title = "Delivering",
                icon = Icons.DELIVERY_DINING,
                # content = TextField(label="Adresse complète", width=300)
            ),
            Step(
                title="Completed",
                icon = Icons.CHECK,
                
            ),
            Step(
                title="Confirmation",
                icon = Icons.VERIFIED,
                # content = Text("Merci ! Votre commande sera traitée.")
            )
        ]

        return Stepper(
            steps = steps,
            orientation = StepperOrientation.HORIZONTAL,
            # on_step_changed=on_step_changed,
            active_color = Colors.ON_SURFACE,
            inactive_color = Colors.GREY_600,
            completed_color = Colors.PRIMARY,
            disabled_color =  Colors.GREY_600,
            title_style = TextStyle(
                size = 10,
                weight = FontWeight.W_500
            ),
            show_titles = True,
            show_subtitles = False,
            show_step_circle = False,
            step_size = 40.0,
            connector_size = 25,
            bgcolor = Colors.SURFACE,
            border_radius = 15
        )
    
    def build_row(self, key, value, size: int = 14):
        """Build row Widget"""

        return Row(
            alignment = MainAxisAlignment.SPACE_BETWEEN,
            controls = [
                Text(
                    key,
                    size = size,
                    weight = FontWeight.W_600
                ),
                Text(
                    f'{value}',
                    size = size,
                    weight = FontWeight.W_600
                ),
            ]
        )

    def build(self)-> Control:
        """Method that build OrderdetailsPage content"""

        # Get Order from navigation
        self.order = self.route_info.data.get('order',None)
        return SafeArea(
            expand = True,
            minimum_padding = 0,
            maintain_bottom_view_padding = False,
            content = Column(
                expand = True,
                # scroll = ScrollMode.AUTO,
                alignment = MainAxisAlignment.START,
                horizontal_alignment = CrossAxisAlignment.CENTER,
                controls = [
                    # HEADER
                    Row(
                        width = self.width,
                        height = 40,
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
                                f"{self.order.code}",
                                size = 16,
                                weight = FontWeight.W_500
                            ),
                            
                            # PLACE HOLDER
                            Container(
                                width = 40
                            )
                        ]
                    ),

                    Column(
                        expand = True,
                        scroll = ScrollMode.AUTO,
                        alignment = MainAxisAlignment.START,
                        horizontal_alignment = CrossAxisAlignment.CENTER,
                        controls = [
                            # ORDER ITEMS
                            Container(
                                # expand = True,
                                height = self.page_instance.height * .48,
                                width = self.width,
                                # bgcolor = 'red',
                                content = ListView(
                                    expand = True,
                                    spacing = 10,
                                    controls = [
                                        Cartitem(
                                            item = item,
                                            read_only = True
                                        )
                                        for item in self.order.articles
                                    ]
                                )
                            ),

                            # STEPPER
                            Container(
                                height = 100,
                                width = self.width,
                                content = self.build_stepper()
                            ),

                            # DETAILS
                            Container(
                                expand = True,
                                width = self.width,
                                content = Column(
                                    alignment = MainAxisAlignment.END,
                                    controls = [
                                        self.build_row('Date', self.order.created.date().isoformat()),
                                        Divider(height=5),
                                        self.build_row('Total Items', len(self.order.articles)),
                                        Divider(height=5),
                                        self.build_row('Transaction', self.order.transaction.code),
                                        Divider(height=5),
                                        self.build_row('Transaction status', self.order.transaction.status),
                                        Divider(height=5),
                                        self.build_row('Total', f'{self.order.total} cfa', size = 18),
                                    ]
                                )
                            ),
                        ]
                    )
                ]
            )
        )