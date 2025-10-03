from dataclasses import dataclass
from typing import Optional

from .base import BaseModel

####
##      BANNER INFO
#####
@dataclass
class BannerInfo(BaseModel):
    """Banner representation model."""

    title: str
    image: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    id: Optional[str] = None