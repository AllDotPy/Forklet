from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Union

from .base import BaseModel


####
##      TRANSACTION INFO
#####
@dataclass
class TransactionInfo(BaseModel):
    """Transaction representation model."""

    amount: Optional[int] = 0
    payment_link: Optional[str] = None
    status: Union[str] = None
    id: Optional[str] = None
    code: Optional[str] = None
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

