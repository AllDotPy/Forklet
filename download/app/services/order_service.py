"""
Order Controller.

This Service class is generated from a template.
"""

from typing import Optional
from fletx.core import FletXService
from fletx.core.http import HTTPClient

from app.models import OrderInfo
from app.utils import get_storage

class OrderService(FletXService):
    """Order Service"""

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
        """Do stuf here on OrderService start"""
        pass
    
    def on_stop(self):
        """Do stuf here on OrderService stop"""
        pass

    def get_token(self, name:str):
        """Return saved token from Client Storage"""

        tokens: dict = (
            get_storage().get('tokens') 
            if get_storage().contains_key('tokens')
            else {}
        )
        return tokens.get(name)
    
    def all(
        self,
        page: int = 0, 
        limit: int = 40,
        query: Optional[str] = '', 
    ):
        """Get All User's order"""

        token = self.get_token('access')

        params = query + '&' if query != '' else query

        filters = f'?{params}offset={page * limit}&limit={limit}'

        return self.http_client.get(
            endpoint = f'/orders/{filters}',
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
        )
    
    def retrieve(self, id: int):
        """Retrieve an Order with a given id"""

        token = self.get_token('access')

        return self.http_client.get(
            endpoint = f'/orders/{id}',
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
        )
    
    def create(self, order: OrderInfo):
        """Create an Order."""

        token = self.get_token('access')

        payload = {
            'articles': [
                {
                    'product': art.product.id,
                    'quantity': art.quantity,
                    'selling_price': art.product.price
                }
                for art in order.articles
            ]
        }

        return self.http_client.post(
            endpoint = f'/orders/',
            json_data = payload,
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
        )

