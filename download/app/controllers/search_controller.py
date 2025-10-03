"""
Search Controller.

This controller class is generated from a template.

🛠️ Customization Guide:
- You can rename or extend this class as needed.
  → Example: Inherit from a different base if you use a custom controller class.
- Add your own reactive attributes using types like `RxInt`, `RxStr`, `RxBool`, etc.
- Implement methods to handle business logic, side effects, or custom events.
- Controllers can be injected into components or apps using dependency injection or manual wiring.
"""

from typing import Optional, List
from fletx import FletX
from fletx.core import (
    FletXController, RxInt, RxBool, RxList, RxDict,
    RxStr
)

from app.models import ProductInfo, SearchFilter
from app.services import ProductsService
from app.utils import get_http_error_message

class SearchController(FletXController):
    """Search Controller"""

    def __init__(self):
        # Defining Product Service
        self.productService: ProductsService = FletX.put(
            ProductsService(), tag = 'product_srv'
        )
        super().__init__()

        self.query: RxStr= self.create_rx_str("")
        self.enabled: RxBool = self.create_rx_bool(False)
        self.filter_enabled: RxBool = self.create_rx_bool(False)
        # self._filter = self.create_reactive(SearchFilter(
        #     name = 
        # ))
        self.search_results: RxList[ProductInfo] = self.create_rx_list([])
        self.recent_search: RxDict[List[ProductInfo]] = self.create_rx_dict({})
        self.current_page: RxInt = self.create_rx_int(0)
        self.has_next: RxBool = self.create_rx_bool(False)
        self.has_previous: RxBool = self.create_rx_bool(False)

    def on_initialized(self):
        """Hook called when initializing controller"""
        print("SearchController initialized.")

    def on_ready(self):
        """Hook called when the controller is ready"""
        print("SearchController is READY!!!")
    
    def on_disposed(self):
        """Hook called when disposing controller"""
        print("SearchController is disposing")

    def perform_search(self):
        """Perform search action."""

        # Build filter options
        options: dict = {'title':self.query.value.strip()}

        if self.filter_enabled.value:
            options |= {
                'categoryID': ''
            }

        # Call filter method with options
        return self.filter(**options)

    def filter(
        self,
        title: Optional[str] = None,
        categoryId: Optional[int] = None,
        categorySlug: Optional[str] = None,
        price: Optional[int] = None,
        price_min: Optional[int] = None,
        price_max: Optional[int] = None,
        page: int = 0,
        limit: int = 40,
    ) -> List[ProductInfo]:
        """Filter products"""

        # Set loading state
        self.set_loading(True)
        result = []

        try:
            # Make the request
            res = self.productService.filter(
                title = title, 
                categoryId = categoryId, 
                categorySlug = categorySlug, 
                price = price, 
                price_min = price_min, 
                price_max = price_max, 
                page = page, 
                limit = limit
            )

            if res.ok and res.is_json:
                data = res.json()
                # Has Previous
                self.has_previous.value = data.get('previous',None) != None
                # Has Next
                self.has_next.value = data.get('next',None) != None
                # Change current page index
                self.current_page.increment()
                # Then parse ans return product list
                result = [
                    ProductInfo.from_json(prod) 
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
            # self.recent_search.clear()
            self.search_results.value = result
            return result
        
# GLOBAL INSTANCE
FletX.put(SearchController(), tag = 'search_ctrl')
