from dataclasses import dataclass
from typing import Optional

from .base import BaseModel
from .product import ProductInfo

####
##      ORDER INFO
#####
@dataclass
class CartItem(BaseModel):
    """Shopping cart Item representation model."""

    product: ProductInfo
    quantity: Optional[int] = 0
    