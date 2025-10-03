"""
Auth Controller.

This Service class is generated from a template.
"""

import httpx
from fletx.core import FletXService
from fletx.core.http import HTTPClient

from app.models import LoginInfo, UserInfo
from app.utils import get_storage


class AuthService(FletXService):
    """Auth Service"""

    def __init__(self, *args, **kwargs):
        self.base_url = "http://localhost:10000"

        # Init base class
        super().__init__(
            http_client = HTTPClient(
                base_url = self.base_url,
                sync_mode = True
            ),
            **kwargs
        )

    def on_start(self):
        """Do stuf here on AuthService start"""
        pass
    
    def on_stop(self):
        """Do stuf here on AuthService stop"""
        pass

    def get_token(self, name:str):
        """Return saved token from Client Storage"""

        tokens: dict = (
            get_storage().get('tokens') 
            if get_storage().contains_key('tokens')
            else {}
        )
        return tokens.get(name)

    def refresh_token(self):
        """Refresh auth tokens"""

        token = self.get_token('access')

        return self.http_client.post(
            endpoint = '/auth/refresh-token',
            json_data = {
                "refreshToken": f"{token}"
            }
        )

    def login(self, cred: LoginInfo):
        """Authenticates user from credential"""

        # build request payload
        payload = {
            'login': cred.phone_number or cred.email,
            'password': cred.password
        }

        # Make request
        return self.http_client.post(
            endpoint = '/auth/login',
            json_data = payload,
            headers = {
                'Content-Type': 'application/json'
            }
        )
    
    def register(self, user: UserInfo):
        """ Register a new user."""

        payload = user.to_json()
        payload.pop('id', None)  # Remove id if exists

        # Make the request
        return self.http_client.post(
            endpoint = '/auth/register',
            json_data = user.to_json(),
            headers = {
                'Content-Type': 'application/json'
            }
        )

    def get_profile(self):
        """Get user profile by a given token."""

        token = self.get_token('access')

        return self.http_client.get(
            endpoint = '/auth/profile',
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
        )
        