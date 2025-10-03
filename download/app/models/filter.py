from dataclasses import dataclass
from typing import Optional

from .base import BaseModel

####
##      SEARCH FILTER INFO
#####
@dataclass
class SearchFilter(BaseModel):
    """Product search filter representation model."""

    name: str
    category_id: Optional[str] = None
    price: Optional[int] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    page: Optional[int] = 0
    limit: Optional[int] = 40
