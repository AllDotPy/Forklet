"""
Categories Controller.

This Service class is generated from a template.
"""

from fletx.core import FletXService
from fletx.core.http import HTTPClient

from app.models import CategoryInfo
from app.utils import get_storage


class CategoriesService(FletXService):
    """Categories Service"""

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
        """Do stuf here on CategoriesService start"""
        pass
    
    def on_stop(self):
        """Do stuf here on CategoriesService stop"""
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
        """Get All Product categories"""

        return self.http_client.get(
            endpoint = '/categories/',
            headers = {
                'Content-Type': 'application/json',
            }
        )
    
    def retrieve(self, id:int):
        """Retrieve category by a given id"""

        # token = self.get_token('access')

        return self.http_client.get(
            endpoint = f'/categories/{id}',
            headers = {
                'Content-Type': 'application/json',
                # 'Authorizations': f'Bearer {token}'
            }
        )
    
    def create(self, category: CategoryInfo):
        """Create a new category from provided infos."""

        token = self.get_token('access')

        payload = {
            "name": category.name,
            "image": category.image
        }

        return self.http_client.post(
            endpoint = f'/categories',
            json_data = payload,
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
        )
    def update(self, id: int, category: CategoryInfo):
        """Upadtes an existing category"""

        token = self.get_token('access')

        payload = {
            "name": category.name,
            "image": category.image
        }

        return self.http_client.put(
            endpoint = f'/categories/{id}',
            json_data = payload,
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
        )
    
    def delete(self,id: int):
        """Delete a category with a given id"""

        token = self.get_token('access')

        return self.http_client.delete(
            endpoint = f'/categories/{id}',
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
        )
    
    def get_category_products(self,id: int):
        """Get all products from a given category."""

        # token = self.get_token('access')

        return self.http_client.delete(
            endpoint = f'/categories/{id}/products',
            headers = {
                'Content-Type': 'application/json',
                # 'Authorizations': f'Bearer {token}'
            }
        )
    