from dataclasses import dataclass
from typing import Optional

from .base import BaseModel


####
##      LOGIN INFO
#####
@dataclass
class LoginInfo(BaseModel):
    """Login credential representation."""

    password: str
    email: Optional[str] = None
    phone_number: Optional[str] = None
    username: Optional[str] = None