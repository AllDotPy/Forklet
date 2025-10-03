"""
User Controller.

This Service class is generated from a template.
"""

from fletx.core import FletXService
from fletx.core.http import HTTPClient

from app.models import UserInfo
from app.utils import get_storage


class UserService(FletXService):
    """User Service"""

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
        """Do stuf here on UserService start"""
        pass
    
    def on_stop(self):
        """Do stuf here on UserService stop"""
        pass

    def get_token(self, name:str):
        """Return saved token from Client Storage"""

        tokens: dict = (
            get_storage().get('tokens') 
            if get_storage().contains_key('tokens')
            else {}
        )
        return tokens.get(name)

    def all(self):
        """Get all users."""

        token = self.get_token('access')

        # Make the request and return its result
        return self.http_client.get(
            endpoint = '/accounts/users',
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
        )
    
    def retrieve(self,id:int):
        """Retrieve user by a given id"""

        token = self.get_token('access')

        # Make the request and return its result
        return self.http_client.get(
            endpoint = f'/accounts/users/{id}',
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
        )
    
    def create(self, user: UserInfo,):
        """Create a new user with a given informations."""

        token = self.get_token('access')
        payload = user.to_json()
        payload.pop('id', None)  # Ensure 'id' is not included in the payload

       # Make the request and return its result
        return self.http_client.post(
            endpoint = f'/accounts/users',
            json_data = user.to_json(),
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
        )
    
    def update(self,id:int , user: UserInfo):
        """Update user informations."""

        token = self.get_token('access')

       # Make the request and return its result
        return self.http_client.put(
            endpoint = f'/accounts/users/{id}',
            json_data = user.to_json(),
            headers = {
                'Content-Type': 'application/json',
                'Authorizations': f'Bearer {token}'
            }
        )
    
    def check_email(self, email:str):
        """Check that a given email is available."""

        payload = {
            'email': email
        }

       # Make the request and return its result
        return self.http_client.post(
            endpoint = f'/accounts/users/is-available',
            json_data = payload,
            headers = {
                'Content-Type': 'application/json',
            }
        )