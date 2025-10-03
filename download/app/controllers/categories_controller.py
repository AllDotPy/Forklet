"""
Categories Controller.

This controller class is generated from a template.

🛠️ Customization Guide:
- You can rename or extend this class as needed.
  → Example: Inherit from a different base if you use a custom controller class.
- Add your own reactive attributes using types like `RxInt`, `RxStr`, `RxBool`, etc.
- Implement methods to handle business logic, side effects, or custom events.
- Controllers can be injected into components or apps using dependency injection or manual wiring.
"""

from typing import List, Optional
from fletx import FletX
from fletx.core import (
    FletXController, RxList
)

from app.services import CategoriesService
from app.models import CategoryInfo, ProductInfo
from app.utils import get_http_error_message

class CategoriesController(FletXController):
    """Categories Controller"""

    def __init__(self):
        # Defining Category Service
        self.categoryService: CategoriesService = FletX.put(
            CategoriesService(), tag = 'category_srv'
        )
        super().__init__()

        # Global categories list
        self.objects: RxList[CategoryInfo] = self.create_rx_list([])

    def on_initialized(self):
        """Hook called when initializing controller"""
        print("CategoriesController initialized.")

    def on_ready(self):
        """Hook called when the controller is ready"""
        print("CategoriesController is READY!!!")
    
    def on_disposed(self):
        """Hook called when disposing controller"""
        print("CategoriesController is disposing")

    def all(self) -> List[CategoryInfo]:
        """Get All Categories."""

        # Set loading state
        self.set_loading(True)
        result = []

        try:
            # Make the request
            res = self.categoryService.all()

            if res.ok and res.is_json:
                # Then parse ans return category list
                result = [
                    CategoryInfo.from_json(cat) 
                    for cat 
                    in res.json().get('results')
                ]

            # If request failed, set error message
            else:
                self.set_error(
                    get_http_error_message(res)
                )

        except Exception as e:
            self.set_error(str(e))

        finally:
            self.set_loading(False)
            self.objects.extend(result)
            return result
        
    def retrieve(self, id: int) -> CategoryInfo:
        """Retrieve a category by a given id"""

        # Set loading state
        self.set_loading(True)
        result = None

        try:
            # Make the request
            res = self.categoryService.retrieve(id)

            if res.ok and res.is_json:
                # Then parse ans return category
                result = CategoryInfo.from_json(res.json())

            # If request failed, set error message
            else:
                self.set_error(
                    get_http_error_message(res)
                )

        except Exception as e:
            self.set_error(str(e))

        finally:
            self.set_loading(False)
            return result
        
    def retrieve_by_slug(self, slug: str) -> CategoryInfo:
        """Retrieve a category by a given slug"""

        # Set loading state
        self.set_loading(True)
        result = None

        try:
            # Make the request
            res = self.categoryService.retrieve_by_slug(slug)

            if res.ok and res.is_json:
                # Then parse ans return category
                result = CategoryInfo.from_json(res.json())

            # If request failed, set error message
            else:
                self.set_error(
                    get_http_error_message(res)
                )

        except Exception as e:
            self.set_error(str(e))

        finally:
            self.set_loading(False)
            return result
        
    def create(
        self, 
        category: CategoryInfo
    ) -> Optional[CategoryInfo]:
        """Create a new category from provided infos."""

        # Set loading state
        self.set_loading(True)
        result = None

        try:
            # Make the request
            res = self.categoryService.create(category)

            if res.ok and res.is_json:
                result = CategoryInfo.from_json(res.json())

            # If request failed, set error message
            else:
                self.set_error(
                    get_http_error_message(res)
                )

        except Exception as e:
            self.set_error(str(e))

        finally:
            self.set_loading(False)
            return result
        
    def update(
        self, 
        id: int, 
        category: CategoryInfo
    ) -> Optional[CategoryInfo]:
        """Update an existing category"""

        # Set loading state
        self.set_loading(True)
        result = None

        try:
            # Make the request
            res = self.categoryService.update(id, category)

            if res.ok and res.is_json:
                result = CategoryInfo.from_json(res.json())

            # If request failed, set error message
            else:
                self.set_error(
                    get_http_error_message(res)
                )

        except Exception as e:
            self.set_error(str(e))

        finally:
            self.set_loading(False)
            return result
        
    def delete(self, id: int) -> bool:
        """Delete a category by a given id"""

        # Set loading state
        self.set_loading(True)
        success = False

        try:
            # Make the request
            res = self.categoryService.delete(id)

            if res.ok:
                success = True

            # If request failed, set error message
            else:
                self.set_error(
                    get_http_error_message(res)
                )

        except Exception as e:
            self.set_error(str(e))

        finally:
            self.set_loading(False)
            return success
        
    def products(self, id: int) -> List[ProductInfo]:
        """Get products of a category with a given id"""

        # Set loading state
        self.set_loading(True)
        result = []

        try:
            # Make the request
            res = self.categoryService.get_category_products(id)

            if res.ok and res.is_json:
                # Then parse ans return product list
                result = [ProductInfo.from_json(prod) for prod in res.json()]

            # If request failed, set error message
            else:
                self.set_error(
                    get_http_error_message(res)
                )

        except Exception as e:
            self.set_error(str(e))

        finally:
            self.set_loading(False)
            return result

# GLOBAL INSTANCE
FletX.put(CategoriesController(), tag = 'category_ctrl')
