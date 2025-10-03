"""
Fakeshop Application Pages module.

This module contains the application Pages.
Version: 0.1.0
"""

from .counter import CounterPage
from .not_found import NotFoundPage
from .onboarding_page import OnboardingPage
from .auth.login_page import LoginPage
from .auth.register_page import RegisterPage
from .main_page import MainPage
from .shared.productdetails_page import ProductDetailsPage
from .shared.notifications_page import NotificationsPage
from .shared.search_page import SearchPage
from .shared.orderdetails_page import OrderDetailsPage
from .shared.checkout_page import CheckoutPage

__all__ = [
    'CounterPage',
    'NotFoundPage',
    'OnboardingPage',
    'LoginPage',
    'RegisterPage',
    'MainPage',
    'ProductDetailsPage',
    'NotificationsPage',
    'SearchPage',
    'OrderDetailsPage',
    'CheckoutPage'
]