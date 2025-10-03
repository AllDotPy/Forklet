"""
Fakeshop App
None

A FletX application.
Author: pro2015
Version: 0.1.0
"""

import os
import flet as ft
from fletx.app import FletXApp
from fletx.navigation import NavigationMode
from app.routes import FakeshopRouter
# from app.services import PaymentService
from app.utils.theme import light_theme, dark_theme

def main():
    """Main entry point for the Fakeshop application."""

    # Lifecycle Hooks 
    async def on_startup(page: ft.Page):
        print("App is running!")
        print(os.getenv('FLETX_DEBUG'))
        page.padding = 0
        page.on_error = lambda e: print(f"Error: {e}")
        # await PaymentService().connect()
    
    def on_shutdown(page: ft.Page):
        print("App is closed!")
    
    # App Configuration
    app = FletXApp(
        title="Fakeshop",
        initial_route = "/",
        debug = True,
        theme = light_theme,
        dark_theme = dark_theme,
        navigation_mode = NavigationMode.VIEWS,
        theme_mode= ft.ThemeMode.SYSTEM,
        window_config = {
            "width": 400,
            "height": 810,
            "resizable": True,
            "maximizable": True
        },
        on_startup = on_startup,
        on_shutdown = on_shutdown
    )

    # Run App
    app.run_async()     # you can use also `app.run()` method. see documetation for more

if __name__ == "__main__":
    main()