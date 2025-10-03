from dataclasses import dataclass
from typing import Optional

from .base import BaseModel

####
##      USER INFO
#####
@dataclass
class UserInfo(BaseModel):
    """User representation model."""

    first_name: str
    last_name: str
    phone_number: str
    email: Optional[str] = None
    avatar: Optional[str] = None
    date_joined: Optional[str] = None
    isa_active: Optional[bool] = True
    is_staff: Optional[bool] = False
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False
    is_deleted: Optional[bool] = False
    password: Optional[str] = None
    id: Optional[str] = None
