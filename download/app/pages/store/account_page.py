"""
Account Controller.

This Page class is generated from a template.
"""

from flet import *
from fletx import FletX
from typing import Dict, Any, List
from fletx.core import FletXPage

# Import your modules here...
from app.controllers import (
    AuthController, UsersController
)
from app.models import UserInfo


class AccountPage(FletXPage):
    """Account Page"""

    def __init__(self):
        super().__init__(
            padding = padding.symmetric(
                horizontal = 10,
                vertical = 0,
            ),
            bgcolor = Theme.scaffold_bgcolor
        )

        # Inject Contaoller
        self.user_controller: UsersController = FletX.find(
            UsersController, tag = 'users_ctrl'
        )
        self.auth_controller: AuthController = FletX.find(
            AuthController, tag = 'auth_ctrl'
        )
        # Current User
        self.user: UserInfo = self.user_controller.get_global_context('user')


        self.sections: List[List[Dict[str,Any]]] = [
            [
                {
                    'name': 'Manage Address',
                    'page': '',
                    'icon': Icons.LOCATION_PIN
                },
                {
                    'name': 'My Orders',
                    'page': '',
                    'icon': Icons.SHOPPING_BASKET_OUTLINED
                },
                {
                    'name': 'My Coupons',
                    'page': '',
                    'icon': Icons.CALENDAR_MONTH_OUTLINED
                },
                {
                    'name': 'Payment Methods',
                    'page': '',
                    'icon': Icons.LOCATION_PIN
                },
            ],
            [
                {
                    'name': 'Wallet',
                    'page': '',
                    'icon': Icons.WALLET_OUTLINED
                },
                {
                    'name': 'Payment Methods',
                    'page': '',
                    'icon': Icons.PAYMENT_OUTLINED
                },
            ],
            [
                {
                    'name': 'Settings',
                    'page': '',
                    'icon': Icons.SETTINGS_ROUNDED
                },
                {
                    'name': 'Help Center',
                    'page': '',
                    'icon': Icons.HELP_CENTER_OUTLINED
                },
            ],
            [
                {
                    'name': 'Logout',
                    'page': '',
                    'icon': Icons.LOGOUT_OUTLINED
                },
                {
                    'name': 'Delete My Account',
                    'page': '',
                    'icon': Icons.DELETE_OUTLINE
                },
            ]
        ]

    def on_init(self):
        """Hook called when AccountPage in initialized"""

        print("AccountPage is initialized")

    def on_destroy(self):
        """Hook called when AccountPage will be unmounted."""

        print("AccountPage is destroyed")

    def build(self)-> Control:
        """Method that build AccountPage content"""

        return Column(
            expand = True,
            spacing = 30,
            alignment = MainAxisAlignment.START,
            horizontal_alignment = CrossAxisAlignment.CENTER,
            controls = [
                # HEADER
                Row(
                    width = self.width,
                    # height = 60,
                    alignment = MainAxisAlignment.CENTER,
                    vertical_alignment = CrossAxisAlignment.CENTER,
                    controls = [
                        Text(
                            f"Profile",
                            size = 16,
                            weight = FontWeight.BOLD
                        ),
                    ]
                ),

                # USER PROFILE SECTION
                Container(
                    ink = True,
                    height = 100,
                    width = self.width,
                    border_radius = 15,
                    padding = 15,
                    bgcolor = Colors.SURFACE,
                    on_click = lambda _: None,

                    content = Row(
                        expand = True,
                        spacing = 10,

                        controls = [
                            CircleAvatar(
                                height = 80,
                                width = 80,
                                foreground_image_src = (
                                        f'{
                                            self.user.avatar if self.user 
                                            else 'https://i.pinimg.com/736x/0b/97/6f/0b976f0a7aa1aa43870e1812eee5a55d.jpg'
                                        }'
                                    )
                            ),

                            # TEXT
                            Column(
                                expand = True,
                                alignment = MainAxisAlignment.CENTER,
                                controls = [
                                    Text(
                                        f"{self.user.first_name +' ' +self.user.last_name if self.user else 'Anonymous user'}",
                                        size = 16,
                                        weight = FontWeight.BOLD
                                    ),
                                    Text(
                                        f"{self.user.phone_number if self.user else '+000 00000000'}",
                                        size = 14,
                                        weight = FontWeight.W_500
                                    ),
                                ]
                            ),

                            # ICON
                            Icon(
                                Icons.CHEVRON_RIGHT_ROUNDED,
                                size = 38,
                                color = Colors.ON_SURFACE
                            )
                        ]
                    )
                ),

                # SECTIONS
                ListView(
                    spacing = 20,
                    expand = True,
                    controls = [
                        Container(
                            # height = 100,
                            width = self.width,
                            border_radius = 15,
                            padding = 15,
                            bgcolor = Colors.SURFACE,

                            content = ListView(
                                spacing = 5,
                                controls = [
                                    Container(
                                        ink = True,
                                        padding = 10,
                                        border_radius = 15,
                                        on_click = lambda _: None,
                                        content = Row(
                                            controls = [
                                                Icon(
                                                    item['icon'],
                                                    size = 24,
                                                    color = Colors.ON_SURFACE
                                                ),
                                                Text(
                                                    item['name'],
                                                    expand = True,
                                                ),
                                                Icon(
                                                    Icons.CHEVRON_RIGHT_ROUNDED,
                                                    size = 24,
                                                    color = Colors.ON_SURFACE
                                                ),
                                            ]
                                        ) 
                                    )
                                    for item in section
                                ]
                            )
                            
                        )
                        for section in self.sections
                    ]
                ),
            ]
        )