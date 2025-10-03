"""
Order Controller.

This controller class is generated from a template.

🛠️ Customization Guide:
- You can rename or extend this class as needed.
  → Example: Inherit from a different base if you use a custom controller class.
- Add your own reactive attributes using types like `RxInt`, `RxStr`, `RxBool`, etc.
- Implement methods to handle business logic, side effects, or custom events.
- Controllers can be injected into components or apps using dependency injection or manual wiring.
"""

from typing import Optional, List, Dict 
from fletx import FletX
from fletx.core import (
    FletXController, RxInt, RxBool,
    RxList
)

from app.services import OrderService
from app.models import OrderInfo
from app.utils import get_http_error_message

class OrderController(FletXController):
    """Order Controller"""

    def __init__(self):
       # Defining Product Service
        self.orderService: OrderService = FletX.put(
            OrderService(), tag = 'order_srv'
        )
        super().__init__()

        # Global Products
        self.objects: RxList[OrderInfo] = self.create_rx_list([])
        self.current_page: RxInt = self.create_rx_int(0)
        self.has_next: RxBool = self.create_rx_bool(False)
        self.has_previous: RxBool = self.create_rx_bool(False)

    def on_initialized(self):
        """Hook called when initializing controller"""
        print("OrderController initialized.")

    def on_ready(self):
        """Hook called when the controller is ready"""
        print("OrderController is READY!!!")
    
    def on_disposed(self):
        """Hook called when disposing controller"""
        print("OrderController is disposing")

    def all(self, page: Optional[int] = None) -> List[OrderInfo]:
        """Get All Orders."""

        # Set loading state
        self.set_loading(True)
        result = []
        page = page if page else self.current_page.value

        try:
            # Make the request
            res = self.orderService.all(page = page)

            if res.ok and res.is_json:
                data = res.json()
                # Has Previous
                self.has_previous.value = data.get('previous',None) != None
                # Has Next
                self.has_next.value = data.get('next',None) != None
                # Change current page index
                self.current_page.increment()
                # Then parse ans return Order list
                result = [
                    OrderInfo.from_json(prod) 
                    for prod 
                    in res.json().get('results')
                ]

            # If request failed, set error message
            else:
                self.set_error(
                    get_http_error_message(res)
                )

        except Exception as e:
            print(e)
            self.set_error(str(e))
        
        # Close loading state finally
        finally:
            self.set_loading(False)
            self.objects.extend(result)
            return result
        
    def retrieve(self, id: int) -> OrderInfo:
        """Retrieve an Order by a given id"""

        # Set loading state
        self.set_loading(True)
        result = None

        try:
            # Make the request
            res = self.orderService.retrieve(id)

            if res.ok and res.is_json:
                # Then parse ans return product info
                result = OrderInfo.from_json(res.json())

            # If request failed, set error message
            else:
                self.set_error(
                    get_http_error_message(res)
                )

        except Exception as e:
            print(e)
            self.set_error(str(e))
        
        # Close loading state finally
        finally:
            self.set_loading(False)
            return result
        
    def create(self, order: OrderInfo) -> OrderInfo:
        """Create a new product with provided information."""

        # Set loading state
        self.set_loading(True)
        result = None

        try:
            # Make the request
            res = self.orderService.create(order)

            if res.ok and res.is_json:
                # Then parse ans return created Order info
                result = OrderInfo.from_json(res.json())

            # If request failed, set error message
            else:
                self.set_error(
                    get_http_error_message(res)
                )

        except Exception as e:
            print(e)
            self.set_error(str(e))
        
        # Close loading state finally
        finally:
            self.set_loading(False)
            return result

# GLOBAL INSTANCE
FletX.put(OrderController(), tag = 'order_ctrl')
