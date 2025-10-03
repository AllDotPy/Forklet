from dataclasses import dataclass, field
from typing import Optional, List

from .base import BaseModel
from .category import CategoryInfo

####
##      PRODUCT MEDIA INFO
#####
@dataclass
class ProductMediaInfo(BaseModel):
    """roducts Medias representation model."""

    id: Optional[str] = None
    code: Optional[str] = None
    file: Optional[str] = None

####
##      PRODUCT INFO
#####
@dataclass
class ProductInfo(BaseModel):
    """Products representation model."""

    name: str
    # slug: str
    price: int
    category: CategoryInfo
    code: Optional[str] = None
    description: Optional[str] = None
    likes: Optional[int] = 0
    has_been_liked: Optional[bool] = False
    medias: List[ProductMediaInfo] = field(default_factory = list)
    id: Optional[str] = None
