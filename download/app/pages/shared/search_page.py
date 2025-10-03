"""
Search Controller.

This Page class is generated from a template.
"""

from flet import *
from fletx import FletX
from fletx.core import FletXPage
from fletx.navigation import go_back
from fletx.widgets import Obx

# Import your modules here...
from app.components import FromTextField, ProductGrid
from app.controllers import SearchController


class SearchPage(FletXPage):
    """Search Page"""

    def __init__(self):
        super().__init__(
            padding = padding.symmetric(
                horizontal = 10,
                vertical = 0,
            ),
            bgcolor = Theme.scaffold_bgcolor,
        )

        # Inject Controllers
        self.search_controller: SearchController = FletX.find(
            SearchController, tag = 'search_ctrl'
        )

    def on_init(self):
        """Hook called when SearchPage in initialized"""

        print("SearchPage is initialized")

    def on_destroy(self):
        """Hook called when SearchPage will be unmounted."""

        print("SearchPage is destroyed")

    def toggle_enabled(self,value: bool = False):
        """Set search enabled state."""

        self.search_controller.enabled.value = value

    def search_history_and_suggestions(self):
        """Build Search history and suggestion widget"""

        return Column(
            expand = True,
            controls = [
                # RECENTS
                Column(
                    controls = [
                        Text(
                            'Recent Search',
                            size = 16,
                            weight = FontWeight.BOLD
                        )

                    ]
                )
            ]
        )
    
    def busy_indicator(self):
        """Busy indicator widget"""

        return Container(
            expand = True,
            bgcolor = Colors.SURFACE,
            border_radius = 15,

            content = Column(
                expand = True,
                alignment = MainAxisAlignment.CENTER,
                horizontal_alignment = CrossAxisAlignment.CENTER,
                controls = [
                    ProgressRing(
                        height = 50,
                        width = 50
                    ),
                    Text(
                        'Searching...'
                    )
                ]
            )
        )

    def build(self)-> Control:
        """Method that build SearchPage content"""

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
                        height = 40,
                        alignment = MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment = CrossAxisAlignment.CENTER,
                        controls = [
                            IconButton(
                                icon = Icons.ARROW_BACK,
                                icon_color = Colors.ON_SURFACE,
                                on_click = lambda _: go_back()
                            ),
                        ]
                    ),

                    # SEARCH BAR AND FILTERS
                    Row(
                        spacing = 15,
                        controls = [
                            # SEARCH BAR
                            Container(
                                height = 50,
                                expand = True,
                                padding = 10,
                                border_radius = 25,
                                bgcolor = Colors.SURFACE,

                                # Content
                                content = FromTextField(
                                    # label = "",
                                    hint_text = "Search for products...",
                                    rx_value = self.search_controller.query,
                                    expand = True,
                                    filled = False,
                                    bgcolor = Colors.TRANSPARENT,
                                    focused_bgcolor = Colors.TRANSPARENT,

                                    # Border
                                    border_radius = 0,
                                    border = InputBorder.NONE,

                                    # Decoration
                                    icon = Icons.SEARCH_OUTLINED,

                                    # Events
                                    on_click = lambda _ : self.toggle_enabled(True),
                                    on_tap_outside = lambda _ : self.toggle_enabled(False),
                                    on_submit = lambda _ : self.search_controller.perform_search()
                                ),
                            ),

                            # FILTER BUTTON
                            Obx(
                                builder_fn = lambda: IconButton(
                                    icon = Icons.TUNE_OUTLINED,
                                    icon_color = (
                                        Colors.ON_SURFACE 
                                        if not self.search_controller.filter_enabled.value 
                                        else Colors.PRIMARY
                                    ),
                                    icon_size = 28,
                                    bgcolor = Colors.SURFACE,

                                    on_click = lambda _: None
                                )
                            )
                        ]
                    ),

                    # CONTENT
                    Obx(
                        builder_fn = lambda: Container(
                            expand = True,
                            width = self.width,
                            # bgcolor = 'red',
                            content = (
                                # self.search_history_and_suggestions()
                                # if self.search_controller.enabled.value 
                                # else 
                                self.busy_indicator() 
                                if self.search_controller._is_loading.value
                                else Column(
                                    expand = True,
                                    alignment = MainAxisAlignment.START,
                                    controls = [
                                        Text("Résultats pour", size=16), 
                                        ProductGrid(
                                            products = self.search_controller.search_results,
                                            spacing = 10,
                                            expand = True,
                                            width = self.width,
                                            padding = padding.symmetric(
                                                vertical = 5,
                                                horizontal = 0
                                            ),
                                            runs_count = 2 if len(self.search_controller.search_results) > 0 else 1,
                                            run_spacing = 5,
                                            child_aspect_ratio = .80,
                                            # height = self.height,
                                        ),
                                        # Text("Résultats pour", size=16),
                                    ]
                                )
                            )
                        )
                    ),
                ]
            )
        )