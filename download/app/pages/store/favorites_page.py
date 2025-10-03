"""
Favorites Controller.

This Page class is generated from a template.
"""

from flet import *
from fletx import FletX
from fletx.core import FletXPage, RxList

# Import your modules here...
from app.components import ProductGrid
from app.controllers import ProductsController, CategoriesController


class FavoritesPage(FletXPage):
    """Favorites Page"""

    def __init__(self):
        super().__init__(
            padding = 10,
            bgcolor = Theme.scaffold_bgcolor
        )

        # ...
        self.productsController: ProductsController = FletX.find(
            ProductsController, tag = 'product_ctrl'
        )
        self.categoryController: CategoriesController = FletX.find(
            CategoriesController, tag = 'category_ctrl'
        )

    def on_init(self):
        """Hook called when FavoritesPage in initialized"""

        print("FavoritesPage is initialized")

    def on_destroy(self):
        """Hook called when FavoritesPage will be unmounted."""

        print("FavoritesPage is destroyed")

    def build_tabs(self):
        """Build Content tab"""

        tabs = Tabs(
            padding = 0,
            selected_index = 1,
            animation_duration = 300,

            # TABS
            tabs = [
                Tab(
                    text = category.name.capitalize(),
                    content = Container(
                        padding = Padding(left = 0, right = 0, top = 10, bottom = 0),
                        content = ProductGrid(
                            products = RxList([]),
                            expand = True
                        )#self.build_category_content(category)
                    )
                )
                for category in self.categoryController.objects.value
            ]
        )

        return tabs

    def build(self)-> Control:
        """Method that build FavoritesPage content"""

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
                            f"My Favorite Products",
                            size = 16,
                            weight = FontWeight.BOLD
                        ),
                    ]
                ),

                self.build_tabs()
                # Text("FavoritesPage works!", size=24),
            ]
        )