"""
Orders Controller.

This Page class is generated from a template.
"""

from flet import *
from typing import List
from fletx import FletX
from fletx.core import FletXPage, RxList

# Import your modules here...
from app.controllers import OrderController
from app.components import (
    OrderList
)
from app.models import OrderInfo, OrderStatus

class OrdersPage(FletXPage):
    """Orders Page"""

    def __init__(self):
        super().__init__(
            padding = padding.symmetric(
                horizontal = 10,
                vertical = 0,
            ),
            bgcolor = Theme.scaffold_bgcolor
        )

        # ...
        self.order_controller: OrderController = FletX.find(
            OrderController, tag = 'order_ctrl'
        )

        self.waiting_payments: RxList[OrderInfo] = self.order_controller.create_rx_list([]) 
        self.delivering: RxList[OrderInfo] = self.order_controller.create_rx_list([]) 
        self.completed: RxList[OrderInfo] = self.order_controller.create_rx_list([]) 

        # Process Orders
        self.process_orders()

    def on_init(self):
        """Hook called when OrdersPage in initialized"""

        print("OrdersPage is initialized")
        self.watch(
            self.order_controller.objects,
            self.process_orders
        )

    def on_destroy(self):
        """Hook called when OrdersPage will be unmounted."""

        print("OrdersPage is destroyed")

    def load_orders(self):
        """Load all data"""

        # Get Categories
        if not (self.order_controller.objects):
            self.order_controller.all()

    def process_orders(self):
        """Group Orders by group based on status"""

        all: List[OrderInfo] = self.order_controller.objects.value

        def find_group(group: OrderStatus):
            nonlocal all

            return [
                o for o in all 
                if o.status.lower().replace('_', ' ') == group.lower().replace('_', ' ')
            ]

        self.waiting_payments.clear() 
        self.waiting_payments.extend(find_group(OrderStatus.WAITING_FOR_PAYMENT))

        self.delivering.clear() 
        self.delivering.extend(find_group(OrderStatus.DELIVERING))

        self.completed.clear()
        self.completed.extend(find_group(OrderStatus.COMPLETED))

    def build_tabs(self):
        """Build Tabs to display Filtered orders."""

        tabs = Tabs(
            expand = True,
            padding = 0,
            selected_index = 0,
            animation_duration = 300,

            # TABS
            tabs = [
                Tab(
                    text = 'All',
                    # tab_content = ,
                    content = Container(
                        expand = True,
                        padding = Padding(left = 0, right = 0, top = 10, bottom = 0),
                        content = Container(
                            expand = True,
                            width = self.width,
                            # bgcolor = 'red',
                            content = OrderList(
                                expand = True,
                                spacing = 10,
                                width = self.width,
                                orders = self.order_controller.objects
                            )
                        ),
                    )
                ),
                Tab(
                    text = OrderStatus.WAITING_FOR_PAYMENT.replace('_',' ').capitalize(),
                    # tab_content = ,
                    content = Container(
                        padding = Padding(left = 0, right = 0, top = 10, bottom = 0),
                        content = # ITEMS
                        Container(
                            expand = True,
                            width = self.width,
                            # bgcolor = 'red',
                            content = OrderList(
                                expand = True,
                                spacing = 10,
                                width = self.width,
                                orders = self.waiting_payments
                            )
                        ),
                    )
                ),
                Tab(
                    text = OrderStatus.DELIVERING.replace('_',' ').capitalize(),
                    # tab_content = ,
                    content = Container(
                        padding = Padding(left = 0, right = 0, top = 10, bottom = 0),
                        content = # ITEMS
                        Container(
                            expand = True,
                            width = self.width,
                            # bgcolor = 'red',
                            content = OrderList(
                                expand = True,
                                spacing = 10,
                                width = self.width,
                                orders = self.delivering
                            )
                        ),
                    )
                ),
                Tab(
                    text = OrderStatus.COMPLETED.replace('_',' ').capitalize(),
                    # tab_content = ,
                    content = Container(
                        padding = Padding(left = 0, right = 0, top = 10, bottom = 0),
                        content = # ITEMS
                        Container(
                            expand = True,
                            width = self.width,
                            # bgcolor = 'red',
                            content = OrderList(
                                expand = True,
                                spacing = 10,
                                width = self.width,
                                orders = self.completed
                            )
                        ),
                    )
                )
                # for state in [
                #     OrderStatus.WAITING_FOR_PAYMENT, 
                #     OrderStatus.DELIVERING, 
                #     OrderStatus.COMPLETED
                # ]
            ]
        )

        return tabs

    def build(self)-> Control:
        """Method that build OrdersPage content"""

        return Column(
            expand = True,
            alignment = MainAxisAlignment.START,
            horizontal_alignment = CrossAxisAlignment.CENTER,
            controls = [
                # HEADER
                Row(
                    width = self.width,
                    height = 40,
                    alignment = MainAxisAlignment.CENTER,
                    vertical_alignment = CrossAxisAlignment.CENTER,
                    controls = [
                        Text(
                            f"My Orders",
                            size = 16,
                            weight = FontWeight.BOLD
                        ),
                    ]
                ),

                # ITEMS
                Container(
                    expand = True,
                    width = self.width,
                    # bgcolor = 'red',
                    content = self.build_tabs()
                ),
            ]
        )