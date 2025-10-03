
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Union

from .base import BaseModel
from .order import OrderInfo


####
##      PAYMENT EVENT INFO
#####
@dataclass
class PaymentEvent(BaseModel):
    """Transaction Event representation model."""

    payload: Optional[OrderInfo] = None
    event_type: Optional[str] = None
    

