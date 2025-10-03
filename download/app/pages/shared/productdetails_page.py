"""
Producrdetails Controller.

This Page class is generated from a template.
"""

from flet import *
from typing import Optional
from fletx import FletX
from fletx.core import FletXPage
from fletx.decorators import obx
from fletx.navigation import go_back
from fletcarousel import (
    BasicAnimatedHorizontalCarousel,
    HintLine, AutoCycle
)

# Import your modules here...
from app.models import ProductInfo
from app.controllers import ProductsController
from app.components import EmptylistComponent


class ProductDetailsPage(FletXPage):
    """Producrdetails Page"""

    def __init__(self):
        # Init Super class
        super().__init__(
            padding = padding.symmetric(
                horizontal = 10,
                vertical = 0,
            ),
            bgcolor = Theme.scaffold_bgcolor,
        )

        # Inject Controllers
        self.productController: ProductsController = FletX.find(
            ProductsController, tag = 'product_ctrl'
        )

        # Attributes initialization
        self.product: Optional[ProductInfo] = None
        self.liked = self.productController.create_rx_bool(False)

    def on_init(self):
        """Hook called when ProducrdetailsPage in initialized"""

        print("ProducrdetailsPage is initialized")
        self.liked.value = self.product.has_been_liked

    def on_destroy(self):
        """Hook called when ProducrdetailsPage will be unmounted."""

        print("ProducrdetailsPage is destroyed")

    def process_like_dislike(self):
        """Process like dislike logic"""

        # toggle like state
        self.liked.toggle()
        action: str = 'post' if not self.liked.value else 'delete'

        res = self.productController.like_or_dislike(
            self.product.id, action = action
        )

        self.product.has_been_liked = self.liked.value

    @obx
    def like_btn(self):
        """Favorite button"""

        return IconButton(
            # top = 10,
            # right = 15,
            bgcolor = Colors.SURFACE,
            on_click = lambda _ : (
                None    #TODO: Call like action with product controller
                if self.productController._is_loading.value
                else self.process_like_dislike()
            ),
            content = (
                ProgressRing(
                    height = 25,
                    width = 25,
                    color = Colors.ON_SURFACE
                )
                if self.productController._is_loading.value
                else Icon(
                    Icons.FAVORITE,
                    color = Colors.ON_SURFACE if not self.liked.value else Colors.PRIMARY,
                ) 
            )
        ) # TODO: CHECK IF USER IS LOGGED IN.

    def build_details_tabs(self):
        """Build Categories"""

        tabs = Tabs(
            padding = 0,
            height = 600,
            scrollable = False,
            selected_index = 0,
            animation_duration = 300,
            label_color = Colors.ON_SURFACE,
            unselected_label_color = Colors.with_opacity(
                .7, Colors.ON_SURFACE
            ),

            # TABS
            tabs = [
                # DESCRIPTION
                Tab(
                    text = 'Description',
                    icon = Icons.DETAILS_OUTLINED,
                    content = Container(
                        padding = Padding(left = 0, right = 0, top = 10, bottom = 0),
                        content = Text(
                            f"{self.product.description}",
                            size = 14,
                            width = self.width,
                            weight = FontWeight.W_400
                        ),
                    )
                ),

                # REVIEWS
                Tab(
                    text = 'Reviews',
                    icon = Icons.RATE_REVIEW_OUTLINED,
                    content = Container(
                        padding = Padding(left = 0, right = 0, top = 10, bottom = 0),
                        content = EmptylistComponent(
                            message = 'No review yet!',
                            # expand = True
                        )
                    )
                ),

                # SIMILAR PRODUCTS
                Tab(
                    text = 'Similar Products',
                    icon = Icons.PROPANE_OUTLINED,
                    content = Container(
                        padding = Padding(left = 0, right = 0, top = 10, bottom = 0),
                        content = EmptylistComponent(
                            message = 'No Similar products found!',
                            # expand = True
                        )
                    )
                )
            ]
        )

        return tabs

    def build(self)-> Control:
        """Method that build ProducrdetailsPage content"""

        self.product = self.route_info.data.get('product',None)

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
                                f"{self.product.name[:20] + '...'}",
                                size = 16,
                                weight = FontWeight.W_500
                            ),
                            
                            # Like button
                            self.like_btn()
                        ]
                    ),

                    Column(
                        expand = True,
                        scroll = ScrollMode.ALWAYS,
                        controls = [
                            # IMAGES
                            BasicAnimatedHorizontalCarousel(
                                # page = self.page_instance,
                                auto_cycle = AutoCycle(duration=4),
                                # expand = True,
                                width = self.width,
                                height = 300,
                                padding = 0,
                                animated_switcher = AnimatedSwitcher(
                                    content = Container(), 
                                    transition = AnimatedSwitcherTransition.FADE, 
                                    duration = 500, 
                                    reverse_duration = 100,
                                ),
                                hint_lines = HintLine(
                                    active_color = Colors.PRIMARY,
                                    inactive_color = Colors.ON_PRIMARY_CONTAINER,
                                    alignment = MainAxisAlignment.CENTER,
                                    max_list_size = 100
                                ),
                                items = [
                                    Image(
                                        src = media.file,
                                        height = 250,
                                        width = self.width,
                                        fit = ImageFit.COVER,
                                        border_radius = 15
                                    )
                                    for media in self.product.medias
                                ],
                            ),

                            #  PRODUCT NAME
                            Text(
                                f"{self.product.name}",
                                max_lines = 2,
                                size = 16,
                                weight = FontWeight.W_500,
                                text_align = TextAlign.LEFT
                            ),

                            # PRICE, CATEGORY, RATING
                            Row(
                                spacing = 10,
                                alignment = MainAxisAlignment.START,
                                controls = [
                                    # PRICE
                                    Text(
                                        f"{self.product.price} FCFA",
                                        size = 18,
                                        color = Colors.PRIMARY,
                                        weight = FontWeight.BOLD,
                                        text_align = TextAlign.LEFT
                                    ),

                                    # CATEGORY
                                    Container(
                                        padding = 10,
                                        border_radius = 20,
                                        bgcolor = Colors.with_opacity(.1, Colors.PRIMARY),
                                        content = Text(
                                            f"{self.product.category.name}",
                                            size = 14,
                                            color = Colors.with_opacity(
                                                .7, Colors.ON_SURFACE
                                            ),
                                            weight = FontWeight.BOLD,
                                            text_align = TextAlign.LEFT
                                        ),
                                    ),

                                    # RATING
                                    Row(
                                        spacing = 0,
                                        alignment = MainAxisAlignment.START,
                                        controls = [
                                            Icon(
                                                Icons.STAR_RATE_ROUNDED,
                                                size = 24,
                                                color = Colors.AMBER_600
                                            ),
                                            Text(
                                                f'4.9',
                                                size = 15,
                                                weight = FontWeight.W_500,
                                                color = Colors.ON_SURFACE_VARIANT
                                            )
                                        ]
                                    )
                                ]
                            ),

                            # DETAILS TABS
                            self.build_details_tabs()
                        ]
                    ),                    
                ]
            )
        )