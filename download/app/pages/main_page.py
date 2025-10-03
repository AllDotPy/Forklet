"""
Main Controller.

This Page class is generated from a template.
"""

import gc
from flet import *
from fletx import FletX
from typing import List, Optional
from fletx.core import FletXPage
# from fletx.decorators import obx
from fletx.widgets import Obx
from app.utils import show_snackbar, show_loader

# Import your modules here...
from .store import (
    HomePage, FavoritesPage,
    ShoppingCartPage, AccountPage,
    OrdersPage
)
from app.controllers import (
    AuthController, ProductsController,
    CategoriesController, OrderController
)


class MainPage(FletXPage):
    """Main Page"""

    def __init__(self):
        super().__init__(
            padding = padding.symmetric(
                horizontal = 0,
                vertical = 0
            ),
            bgcolor = Theme.scaffold_bgcolor
        )

        # Inject Controllers
        self.auth_controller: AuthController = FletX.find(
            AuthController, tag = 'auth_ctrl'
        )
        self.products_controller: ProductsController = FletX.find(
            ProductsController, tag = 'product_ctrl'
        )
        self.categories_controller: CategoriesController = FletX.find(
            CategoriesController, tag = 'category_ctrl'
        )
        self.order_controller: OrderController = FletX.find(
            OrderController, tag = 'order_ctrl'
        )

        self.current_index = self.auth_controller.create_rx_int(0)

        # Store current page content
        self.page_content: Optional[FletXPage] = None

        # self.load_data()

        # Build first content
        self.change_content(
            self.current_index.value
        )

    def on_init(self):
        """Hook called when MainPage in initialized"""

        print("MainPage is initialized")
        # Build NavigationBar
        self.build_navigation()

        # watch index fo rebuild the page content
        self.watch(
            self.current_index,
            lambda: self.change_content(
                self.current_index.value,
                update = True
            )
        )

        self.setup_reactivity()
        
    def on_destroy(self):
        """Hook called when MainPage will be unmounted."""

        print("MainPage is destroyed")

    def load_data(self):
        """Load all data"""

        # Get Categories
        if not (self.categories_controller.objects):
            self.categories_controller.all()

        # Products
        if not len(self.products_controller.objects) > 0:
            self.products_controller.all()
        
        # Orders
        if not len(self.order_controller.objects) > 0:
            self.order_controller.all()

    def setup_reactivity(self):
        """Setup Ui reactivity observers"""

        # Data Loading
        self.watch(
            self.auth_controller._is_loading,
            lambda: show_loader(
                controller = self.auth_controller,
                page = self.page_instance,
                message = 'Please wait a second.'
            ),
            immediate = True,
        )
        self.watch(
            self.categories_controller._is_loading,
            lambda: show_loader(
                controller = self.categories_controller,
                page = self.page_instance
            ),
            immediate = True,
        )
        # self.watch(
        #     self.products_controller._is_loading,
        #     lambda: show_loader(
        #         controller = self.products_controller,
        #         page = self.page_instance
        #     ),
        #     immediate = True,
        # )
        
        # Errors
        self.watch(
            self.auth_controller._error_message,
            lambda: show_snackbar(
                type = 'error',
                page = self.page_instance,
                title = 'Oopss an error occrus!',
                message = self.auth_controller._error_message.value
            ) if self.auth_controller._error_message.value != '' else None,
            immediate = True
        )
        self.watch(
            self.categories_controller._error_message,
            lambda: show_snackbar(
                type = 'error',
                page = self.page_instance,
                title = 'Oopss an error occrus!',
                message = self.categories_controller._error_message.value
            ) if self.categories_controller._error_message.value != '' else None,
            immediate = True
        )
        self.watch(
            self.products_controller._error_message,
            lambda: show_snackbar(
                type = 'error',
                page = self.page_instance,
                title = 'Oopss an error occrus!',
                message = self.products_controller._error_message.value
            ) if self.products_controller._error_message.value != '' else None,
            immediate = True
        )
        self.watch(
            self.order_controller._error_message,
            lambda: show_snackbar(
                type = 'error',
                page = self.page_instance,
                title = 'Oopss an error occrus!',
                message = self.order_controller._error_message.value
            ) if self.order_controller._error_message.value != '' else None,
            immediate = True
        )

    def change_content(self,index: int = 0, update: bool = False):
        """Change page content"""

        pages: List[FletXPage] = [
            HomePage(),
            FavoritesPage(),
            ShoppingCartPage(),
            OrdersPage(),
            AccountPage(),
        ]

        # Dispose existing page content
        if self.page_content:
            self.page_content.will_unmount()
            self.page_content.dispose()
            # gc.collect()# self.page_content

        self.page_content = pages[index]
        self.page_content._build_page()

        if update:
            # self._build_page()
            self.content.content = self.page_content
            self.content.update()

        # return page_content

    def change_index(self, new_idx:int):
        """Change current Page Index"""
        self.current_index.value = new_idx

    def build_navigation(self):
        """Method that build MainPage navigation"""

        self.page_instance.views[-1].navigation_bar = NavigationBar(
            selected_index = 0,
            elevation = 50,
            bgcolor = Colors.SURFACE,
            indicator_color = Colors.PRIMARY,
            width = self.width,
            height = 80,
            on_change = lambda e: self.change_index(int(e.data)), 
            destinations = [
                NavigationBarDestination(
                    icon = Icons.STORE_MALL_DIRECTORY_OUTLINED,
                    selected_icon = Icon(
                        Icons.STORE_MALL_DIRECTORY,
                        color = Colors.ON_PRIMARY
                    ),
                    label = "Store"
                ),
                NavigationBarDestination(
                    icon = Icons.FAVORITE_BORDER_OUTLINED,
                    selected_icon = Icon(
                        Icons.FAVORITE,
                        color = Colors.ON_PRIMARY
                    ),
                    label = "Favorites"
                ),
                NavigationBarDestination(
                    icon = Stack(
                        expand = True,
                        clip_behavior = ClipBehavior.NONE,
                        controls = [
                            Icon(
                                Icons.SHOPPING_CART_OUTLINED,
                                # color = Colors.ON_PRIMARY
                            ),
                            Obx(
                                builder_fn = lambda: Container(
                                    top = -15,
                                    right = -15,
                                    padding = 2,
                                    border_radius = 20,
                                    bgcolor = Colors.ERROR,
                                    width = max(25,len(f'{len(self.products_controller.shopping_cart.value)}') * 15),
                                    visible = len(self.products_controller.shopping_cart.value) != 0,
                                    content = Text(
                                        f'{len(self.products_controller.shopping_cart.value)}',
                                        size = 14,
                                        weight = FontWeight.BOLD,
                                        color = Colors.ON_PRIMARY,
                                        text_align = TextAlign.CENTER,
                                        width = max(25,len(f'{len(self.products_controller.shopping_cart.value)}') * 15),
                                    )
                                )
                            )
                        ]
                    ),
                    selected_icon = Stack(
                        expand = True,
                        clip_behavior = ClipBehavior.NONE,
                        controls = [
                            Icon(
                                Icons.SHOPPING_CART,
                                color = Colors.ON_PRIMARY
                            ),
                            Obx(
                                builder_fn = lambda: Container(
                                    top = -15,
                                    right = -15,
                                    padding = 2,
                                    border_radius = 20,
                                    bgcolor = Colors.ERROR,
                                    width = max(25,len(f'{len(self.products_controller.shopping_cart.value)}') * 15),
                                    visible = len(self.products_controller.shopping_cart.value) != 0,
                                    content = Text(
                                        f'{len(self.products_controller.shopping_cart.value)}',
                                        size = 14,
                                        weight = FontWeight.BOLD,
                                        color = Colors.ON_PRIMARY,
                                        text_align = TextAlign.CENTER,
                                        width = max(25,len(f'{len(self.products_controller.shopping_cart.value)}') * 15),
                                    )
                                )
                            )
                        ]
                    ),
                    label = "Cart"
                ),
                NavigationBarDestination(
                    icon = Icons.SHOPPING_BAG_OUTLINED,
                    selected_icon = Icon(
                        Icons.SHOPPING_BAG,
                        color = Colors.ON_PRIMARY
                    ),
                    label = "Orders"
                ),
                NavigationBarDestination(
                    icon = Icons.PERSON_OUTLINE,
                    selected_icon = Icon(
                        Icons.PERSON,
                        color = Colors.ON_PRIMARY
                    ),
                    label = "Profile"
                )
            ]
        )
        self.page_instance.update()
    
    def build(self)-> Control:
        """Method that build MainPage content"""
        return SafeArea(
            expand = True,
            minimum_padding = 0,
            maintain_bottom_view_padding = False,
            content = self.page_content
        )
