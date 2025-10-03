"""
Home Page.

This Page class is generated from a template.
"""

from flet import *
from fletx import FletX
from fletx.core import FletXPage, RxList, RxBool
from fletx.decorators import obx
from fletx.navigation import navigate
from fletcarousel import (
    BasicAnimatedHorizontalCarousel,
    AutoCycle, HintLine
)

# Import your modules here...
from app.controllers import (
    UsersController, ProductsController,
    CategoriesController, AuthController
)

from app.components import (
    FromTextField, Bannerlist, CategoryList,
    Bannercard, ProductCard, ProductGrid
)
from app.models import UserInfo, ProductInfo
from app.utils import BANNERS

# Import your modules here...


class HomePage(FletXPage):
    """Home Page"""

    def __init__(self):
        super().__init__(
            padding = padding.symmetric(
                horizontal = 10,
                vertical = 0,
            ),
            bgcolor = Theme.scaffold_bgcolor,
        )
        # self.width = 300

        # Initializing Reactives
        self.user: UserInfo
        self.banners: RxList = RxList(BANNERS)
        self.categories: RxList = RxList([])
        self.products: RxList = RxList([])
        self.load_more_clicked = False

        # Initialize Controllers
        self.usersController: UsersController = FletX.find(
            UsersController, tag = 'users_ctrl'
        )
        self.productsController: ProductsController = FletX.find(
            ProductsController, tag = 'product_ctrl'
        )
        self.categoryController: CategoriesController = FletX.find(
            CategoriesController, tag = 'category_ctrl'
        )

        # Load Data
        self.setup_resources()

    def on_init(self):
        """Hook called when HomePage in initialized"""

        print("HomePage is initialized")

        # Setup cleanups
        self.add_cleanup(
            self.categories.dispose
        )
        self.add_cleanup(
            self.banners.dispose
        )

    def on_destroy(self):
        """Hook called when HomePage will be unmounted."""

        print("HomePage is destroyed")

    def setup_resources(self):
        """Load All needed data"""
        # Get Current User
        self.user = self.categoryController.get_global_context(
            'user'
        )
        # Categories
        self.categories = self.categoryController.objects
        
        # Products
        self.products = self.productsController.objects
            
    def build_categories_tabs(self):
        """Build Categories"""

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
                        content = self.build_category_content(category)
                    )
                )
                for category in self.categories.value
            ]
        )

        return tabs
    
    def build_category_content(self,category:str):
        """Get category news from controller"""

        return GridView(
            spacing = 10,
            padding = padding.symmetric(
                vertical = 5,
                horizontal = 0
            ),
            runs_count = 2,
            run_spacing = 5,
            child_aspect_ratio = .80,
            height = self.height,
            controls = [
                ProductCard(
                    padding = 0,
                    expand = True,
                    border_radius = 10,
                    product = product
                ) 
                for product in self.products
            ]
        )

    @obx
    def load_more_button(self):
        """Load more button"""
        return IconButton(
            on_click = lambda _: (
                self.load_more() if (
                    not self.productsController._is_loading.value
                    and not self.load_more_clicked
                ) else None
            ),
            content = (
                ProgressRing(
                    height = 25,
                    width = 25,
                    color = Colors.ON_SURFACE
                )
                if self.productsController._is_loading.value and self.load_more_clicked
                else Text(
                    'load more...' if self.productsController.has_next.value else 'No more data'
                ) 
            )
        )
    
    def load_more(self):
        """Load more products."""

        self.load_more_clicked = True

        # Automatically load next page if exists
        if self.productsController.has_next: 
            self.productsController.all() 

        self.load_more_clicked = False

    def build(self)-> Control:
        """Method that build HomePage content"""

        return Column(
            expand = True,
            # scroll = ScrollMode.HIDDEN,
            alignment = MainAxisAlignment.START,
            horizontal_alignment = CrossAxisAlignment.CENTER,
            controls = [
                # HEADER
                Row(
                    width = self.width,
                    # height = 60,
                    alignment = MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment = CrossAxisAlignment.CENTER,
                    controls = [
                        Row(
                            spacing = 8,
                            expand = True,
                            alignment = MainAxisAlignment.START,
                            controls = [
                                CircleAvatar(
                                    height = 50,
                                    width = 50,
                                    bgcolor = Colors.SURFACE,
                                    foreground_image_src = (
                                        f'{
                                            self.user.avatar if self.user 
                                            else 'https://i.pinimg.com/736x/0b/97/6f/0b976f0a7aa1aa43870e1812eee5a55d.jpg'
                                        }'
                                    )
                                ),
                                Column(
                                    spacing = 2,
                                    alignment = MainAxisAlignment.CENTER,
                                    controls = [
                                        Text(
                                            f"Welcome",
                                            size = 14,
                                            weight = FontWeight.W_400
                                        ),
                                        Text(
                                            f"Hey, {self.user.first_name if self.user else 'Pythonista'}!",
                                            size = 16,
                                            weight = FontWeight.W_500
                                        )
                                    ]
                                ),
                            ]
                        ),

                        # SEARCH BUTTON
                        IconButton(
                            # icon = Icons.SEARCH_OUTLINED,
                            padding = 0,
                            icon_color = Colors.ON_SURFACE,
                            on_click = lambda _: navigate('/search'),
                            content = Container(
                                height = 40,
                                width = 40,
                                border_radius= 20,
                                bgcolor = Colors.SURFACE,
                                border = Border(
                                    top = BorderSide(
                                        color = Colors.GREY_700,
                                        width = 1
                                    ),
                                    bottom = BorderSide(
                                        color = Colors.GREY_700,
                                        width = 1
                                    ),
                                    left = BorderSide(
                                        color = Colors.GREY_700,
                                        width = 1
                                    ),
                                    right = BorderSide(
                                        color = Colors.GREY_700,
                                        width = 1
                                    )
                                ),

                                content = Icon(
                                    Icons.SEARCH_OUTLINED,
                                    size = 24,
                                    weight = 1,
                                    color = Colors.ON_SURFACE
                                )
                            )
                        ),
                        
                        # NOTIFICATION
                        IconButton(
                            # icon = Icons.NOTIFICATIONS_NONE_OUTLINED,
                            # icon_color = Colors.ON_SURFACE,
                            padding = 0,
                            on_click = lambda _: navigate('/notifications'),
                            content = Container(
                                height = 40,
                                width = 40,
                                border_radius= 20,
                                bgcolor = Colors.SURFACE,
                                border = Border(
                                    top = BorderSide(
                                        color = Colors.GREY_700,
                                        width = 1
                                    ),
                                    bottom = BorderSide(
                                        color = Colors.GREY_700,
                                        width = 1
                                    ),
                                    left = BorderSide(
                                        color = Colors.GREY_700,
                                        width = 1
                                    ),
                                    right = BorderSide(
                                        color = Colors.GREY_700,
                                        width = 1
                                    )
                                ),

                                content = Icon(
                                    Icons.NOTIFICATIONS_NONE_OUTLINED,
                                    size = 24,
                                    weight = 1,
                                    color = Colors.ON_SURFACE
                                )
                            )
                        )
                    ]
                ),

                # PAGE CONTENT
                Column(
                    expand = True,
                    scroll = ScrollMode.HIDDEN,
                    horizontal_alignment = CrossAxisAlignment.CENTER,
                    controls = [
                        # SEARCH BAR
                        Container(
                            height = 50,
                            padding = 10,
                            border_radius = 25,
                            bgcolor = Colors.SURFACE,
                            visible = False,
                            on_click = lambda _: navigate('/search'),

                            # Content
                            content = FromTextField(
                                # label = "",
                                hint_text = "Search for products...",
                                # rx_value = self.rx_first_name,
                                expand = True,
                                disabled = True,
                                filled = False,
                                rx_disabled = RxBool(True),
                                bgcolor = Colors.TRANSPARENT,
                                focused_bgcolor = Colors.TRANSPARENT,

                                # Border
                                border_radius = 0,
                                border = InputBorder.NONE,

                                # Decoration
                                icon = Icons.SEARCH_OUTLINED
                            ),
                        ),

                        # SPACER
                        Container(
                            height = 20
                        ),

                        # BANNERS
                        BasicAnimatedHorizontalCarousel(
                            # page = self.page_instance,
                            auto_cycle = AutoCycle(duration=4),
                            expand = True,
                            width = self.width,
                            padding = 0,
                            animated_switcher = AnimatedSwitcher(
                                content = Control(), 
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
                            items=[
                                Bannercard(
                                    item = i,
                                    width = self.width
                                )
                                for i in self.banners.value
                            ],
                        ),

                        # Container(
                        #     height = 150,
                        #     width = self.width,
                        #     content = Bannerlist(
                        #         spacing = 15,
                        #         expand = True,
                        #         # height = 150,
                        #         width = self.width,
                        #         horizontal = True,
                        #         items = self.banners,
                        #     )
                        # ),

                        # SPACER
                        Container(
                            height = 15
                        ),

                        # CATEGORIES
                        Column(
                            width = self.width,
                            controls = [
                                Row(
                                    # expand = True,
                                    alignment = MainAxisAlignment.SPACE_BETWEEN,
                                    vertical_alignment = CrossAxisAlignment.CENTER,
                                    controls = [
                                        Text("Categories", size=16, weight=FontWeight.W_500),
                                        IconButton(
                                            icon_color=Colors.ON_PRIMARY_CONTAINER,
                                            on_click = lambda e: navigate('/categories'),

                                            content = Row(
                                                controls = [
                                                    Text("See all", size=14, weight=FontWeight.W_500),
                                                    Icon(Icons.ARROW_FORWARD, size=16, color=Colors.ON_PRIMARY_CONTAINER)
                                                ]
                                            )
                                        )
                                    ]
                                ),

                                # CATEGORY LIST
                                Container(
                                    height = 120,
                                    width = self.width,
                                    # bgcolor = 'red',
                                    content = CategoryList(
                                        spacing = 20,
                                        expand = True,
                                        horizontal = True,
                                        categories = self.categories
                                    )
                                )
                            ]
                        ),

                        # SPACER
                        Container(
                            height = 20
                        ),

                        # BEST SELLERS
                        Column(
                            width = self.width,
                            controls = [
                                Row(
                                    # expand = True,
                                    alignment = MainAxisAlignment.SPACE_BETWEEN,
                                    vertical_alignment = CrossAxisAlignment.CENTER,
                                    controls = [
                                        Text("Best Seller Products", size=16, weight=FontWeight.W_500),
                                        IconButton(
                                            icon_color=Colors.ON_PRIMARY_CONTAINER,
                                            on_click = lambda e: navigate('/categories'),

                                            content = Row(
                                                controls = [
                                                    Text("See all", size=14, weight=FontWeight.W_500),
                                                    Icon(Icons.ARROW_FORWARD, size=16, color=Colors.ON_PRIMARY_CONTAINER)
                                                ]
                                            )
                                        )
                                    ]
                                ),

                                # CATEGORY LIST
                                Container(
                                    height = 220,
                                    width = self.width,
                                    # bgcolor = 'red',
                                    content = ListView(
                                        spacing = 10,
                                        expand = True,
                                        horizontal = True,
                                        controls = [
                                            ProductCard(product = product)
                                            for product in self.products.value[:10]
                                        ]
                                    )
                                )
                            ]
                        ),

                        # SPACER
                        Container(
                            height = 20
                        ),

                        # LATEST PRODUCTS
                        Column(
                            width = self.width,
                            controls = [
                                Row(
                                    # expand = True,
                                    alignment = MainAxisAlignment.SPACE_BETWEEN,
                                    vertical_alignment = CrossAxisAlignment.CENTER,
                                    controls = [
                                        Text("Latest Products", size=16, weight=FontWeight.W_500),
                                        IconButton(
                                            icon_color=Colors.ON_PRIMARY_CONTAINER,
                                            on_click = lambda e: navigate('/products/latest'),

                                            content = Row(
                                                controls = [
                                                    Text("See all", size=14, weight=FontWeight.W_500),
                                                    Icon(Icons.ARROW_FORWARD, size=16, color=Colors.ON_PRIMARY_CONTAINER)
                                                ]
                                            )
                                        )
                                    ]
                                ),

                                # CATEGORY LIST
                                Container(
                                    height = 220,
                                    width = self.width,
                                    # bgcolor = 'red',
                                    content = ListView(
                                        spacing = 10,
                                        expand = True,
                                        horizontal = True,
                                        controls = [
                                            ProductCard(product = product)
                                            for product in self.products.value[10:20]
                                        ]
                                    )
                                )
                            ]
                        ),

                        # SPACER
                        Container(
                            height = 20
                        ),

                        Row(
                            # expand = True,
                            alignment = MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment = CrossAxisAlignment.CENTER,
                            controls = [
                                Text("Browse Our Products", size=16, weight=FontWeight.W_500),
                                IconButton(
                                    icon_color=Colors.ON_PRIMARY_CONTAINER,
                                    on_click = lambda e: navigate('/products'),

                                    content = Row(
                                        controls = [
                                            Text("See all", size=14, weight=FontWeight.W_500),
                                            Icon(Icons.ARROW_FORWARD, size=16, color=Colors.ON_PRIMARY_CONTAINER)
                                        ]
                                    )
                                )
                            ]
                        ),

                        # PRODUCTS GRID
                        ProductGrid(
                            products = self.products,
                            spacing = 10,
                            expand = True,
                            width = self.width,
                            padding = padding.symmetric(
                                vertical = 5,
                                horizontal = 0
                            ),
                            runs_count = 2,
                            run_spacing = 5,
                            child_aspect_ratio = .80,
                            height = self.height,
                            build_controls_on_demand = True,
                            cache_extent = 10
                        ),

                        # SPACER
                        Container(
                            height = 10
                        ),

                        self.load_more_button()

                        # self.build_categories_tabs(),

                        # Text("MainPage works!", size=24),
                    ]
                ),

            ]
        )