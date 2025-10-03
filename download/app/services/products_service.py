"""
Products Controller.

This Service class is generated from a template.
"""

from typing import Optional
from fletx.core import FletXService
from fletx.core.http import HTTPClient

from app.models import ProductInfo
from app.utils import get_storage


class ProductsService(FletXService):
    """Products Service"""

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
        """Do stuf here on ProductsService start"""
        pass
    
    def on_stop(self):
        """Do stuf here on ProductsService stop"""
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
        """List All products with pagination support."""

        params = query + '&' if query != '' else query

        filters = f'?{params}offset={page * limit}&limit={limit}'

        return self.http_client.get(
            endpoint = f'/products/{filters}',
            headers = {
                'Content-Type': 'application/json',
            }
        )
    
    def retrieve(self, id: int):
        """Retrieve a product with a given id"""

        # token = self.get_token('access')

        return self.http_client.get(
            endpoint = f'/products/{id}',
            headers = {
                'Content-Type': 'application/json',
                # 'Authorization': f'Bearer {token}'
            }
        )
    
    def filter(
        self,
        title: Optional[str] = None,
        categoryId: Optional[int] = None,
        categorySlug: Optional[str] = None,
        price: Optional[int] = None,
        price_min: Optional[int] = None,
        price_max: Optional[int] = None,
        page: Optional[int] = 0,
        limit: Optional[int] = 40,
    ):
        """Filter products"""

        qstr = ''

        # Apply title
        if title:
            qstr += f'search={title}'

        # Category By ID
        if categoryId:
            qstr += f'&category__id={categoryId}'

        # Category Slug
        # if categorySlug:
        #     qstr += f'&categorySlug={categorySlug}'

        # Price
        if price:
            qstr += f'&price={price}'

        # Price min
        elif price_min:
            qstr += f'&price__gte={price_min}'

        # Price max
        elif price_max:
            qstr += f'&price__lte={price_max}'

        return self.all(
            page = page, limit = limit,
            query = qstr
        )

    
    def get_related(self, id: int):
        """Get products Realted to a product with a given id"""

        return self.http_client.get(
            endpoint = f'/products/{id}/relatted',
            headers = {
                'Content-Type': 'application/json',
            }
        )
    
    def create(self, product: ProductInfo):
        """Create a new Product from a given informations"""

        token = self.get_token('access')

        payload = {
            "title": product.title,
            "price": product.price,
            "description": product.desctiotion,
            "categoryId": product.category.id,
            "images": product.images
        }

        return self.http_client.post(
            endpoint = f'/products',
            json_data = payload,
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
        )
    
    def update(self, id: int, product: ProductInfo):
        """Updates a given id product with provided informastions."""

        token = self.get_token('access')

        return self.http_client.put(
            endpoint = f'/products/{id}',
            json_data = product.to_json(),
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
        )
    
    def delete(self, id: int):
        """Delete a product with a given id"""

        token = self.get_token('access')

        return self.http_client.delete(
            endpoint = f'/products/{id}',
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
        )
    
    def like(self, id: str, action: str = 'post'):
        """Perform Like/dislike action on a product."""

        token = self.get_token('access')

        return self.http_client.request(
                method = action,
                endpoint = f'/products/{id}/like',
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {token}'
                }
            ) 
