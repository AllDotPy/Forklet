"""Utility functions"""
from flet import *
from fletx.core import FletXController
from fletx.core.http import HTTPResponse
from fletx.utils import get_page

from .banners import BANNERS

####    GET CLIENT STORAGE
def get_storage():
    """Return Running Page's Client Storage"""

    return get_page().client_storage

####    GET HTTP ERROR MESSAGE
def get_http_error_message(res: HTTPResponse):
    """Return HTTP Error Message based on status code"""

    data = res.json() if res.is_json else {}
    error_msg = data.get('message').get('en')

    if res.status == 400:
        return f"Bad Request, {error_msg}\nplease check your input."
    
    if res.status == 401:
        return f"Unauthorized, {error_msg}\nplease log in again."
    
    if res.status == 403:
        return "Forbidden, you don't have permission to access this resource."
    
    if res.status == 404:
        return "The resource you were looking for could not be found."
    
    if res.status == 500:
        return "Internal Server Error, please try again later."
    
    return "An unexpected error occurred, please try again later."

####    SHOW LOADER
def show_loader(
    controller: FletXController,
    page: Page,
    message: str = 'loading data',
):
        """Show loading when controller is in loading state."""

        if hasattr(show_loader,'dlg'):
            dlg = getattr(show_loader,'dlg')

        else: 
            dlg = AlertDialog(
                content_padding = 10,
                title = Text(
                    message,
                    size = 14,
                    text_align = TextAlign.CENTER
                ),
                content = Row(
                    expand = True,
                    alignment = MainAxisAlignment.CENTER,
                    vertical_alignment = CrossAxisAlignment.CENTER,
                    controls = [
                        ProgressRing(
                            width=40, height=40
                        ),
                    ]
                ),
                alignment = alignment.center,
                on_dismiss = lambda e: print("Dialog dismissed!"),
                title_padding = padding.all(10),
            )
            show_loader.dlg = dlg

        if controller._is_loading.value:
            page.open(dlg)

        else: 
            page.close(dlg)

        
####   SHOW SNACKBAR
def show_snackbar(
    page: Page,
    title: str, 
    message: str, 
    type: str = 'info'
):
    """Show a snackbar"""

    bg = Colors.PRIMARY

    def get_icon():
        nonlocal type
        nonlocal bg

        if type == 'info':
            return Icons.INFO_OUTLINE_ROUNDED
        
        if type == 'error':
            bg = Colors.ERROR_CONTAINER
            return Icons.ERROR_OUTLINE_ROUNDED
        
        if type == 'warning':
            bg = Colors.AMBER_800
            return Icons.WARNING_AMBER_OUTLINED
        
        if type == 'success':
            bg = Colors.TEAL_400
            return Icons.EMOJI_EMOTIONS_OUTLINED
        
        return Icons.FAVORITE_BORDER_OUTLINED
    
    right_icon = get_icon()

    snack = SnackBar(
        bgcolor = Colors.TRANSPARENT,
        content = Container(
            expand = True,
            padding = 10,
            bgcolor = bg,
            border_radius = 20,
            content = Row(
                expand = True,
                alignment = MainAxisAlignment.START,
                vertical_alignment = CrossAxisAlignment.CENTER,
                controls = [
                    # RIGHT ICON
                    Icon(
                        right_icon,
                        size = 40,
                    ),
                    
                    # TEXTS
                    Column(
                        expand = True,
                        alignment = MainAxisAlignment.CENTER,
                        horizontal_alignment = CrossAxisAlignment.START,

                        controls = [
                            Text(
                                title[:50] ,
                                color = Colors.ON_SURFACE,
                                size = 16,
                                max_lines = 2,
                                weight = FontWeight.W_600
                            ),
                            Text(
                                message[:150],
                                color = Colors.ON_SURFACE,
                                size = 12,
                                max_lines = 3,
                                weight = FontWeight.W_400
                            )
                        ]
                    )
                ]
            )
        )
    )

    page.open(snack)