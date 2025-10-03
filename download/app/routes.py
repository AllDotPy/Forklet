"""
fakeShop Application routing module.
Version: 0.1.0
"""


# Import your pages here
from fletx.navigation import (
    ModuleRouter, TransitionType, RouteTransition
)
from fletx.decorators import register_router

from .pages import (
    CounterPage, NotFoundPage,
    OnboardingPage, LoginPage,
    RegisterPage, MainPage,
    ProductDetailsPage,
    SearchPage, NotificationsPage,
    OrderDetailsPage, CheckoutPage,
    store
)

# Define Fakeshop routes here
routes = [
    {
        'path': '/',
        'component': OnboardingPage,
    },

    # AUTHENTICATION URLS
    {
        'path': '/login',
        'component': LoginPage
    },
    {
        'path': '/register',
        'component': RegisterPage
    },

    # STORE URLS
    {
        'path': '/home',
        'component': MainPage
    },
    {
        'path': '/product-details',
        'component': ProductDetailsPage
    },
    {
        'path': '/search',
        'component': SearchPage
    },
    {
        'path': '/order-details',
        'component': OrderDetailsPage
    },
    {
        'path': '/checkout',
        'component': CheckoutPage
    },

    # ACCOUNT URLS
    {
        'path': '/profile',
        'component': store.AccountPage
    },

    # UTILITY URLS
    {
        'path': '/notifications',
        'component': NotificationsPage
    },
    {
        'path': '/counter',
        'component': CounterPage
    },
    {
        'path': '/**',
        'component': NotFoundPage,
    },
]

@register_router
class FakeshopRouter(ModuleRouter):
    """fakeShop Routing Module."""

    name = 'fakeShop'
    base_path = '/'
    is_root = True
    routes = routes
    sub_routers = []