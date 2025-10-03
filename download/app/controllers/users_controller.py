"""
Users Controller.

This controller class is generated from a template.

🛠️ Customization Guide:
- You can rename or extend this class as needed.
  → Example: Inherit from a different base if you use a custom controller class.
- Add your own reactive attributes using types like `RxInt`, `RxStr`, `RxBool`, etc.
- Implement methods to handle business logic, side effects, or custom events.
- Controllers can be injected into components or apps using dependency injection or manual wiring.
"""

from typing import Optional
from fletx import FletX
from fletx.core import (
    FletXController,
)

from app.models import UserInfo
from app.services import UserService
from app.utils import get_http_error_message

class UsersController(FletXController):
    """Users Controller"""

    def __init__(self):
        # Defining User Service
        self.userService: UserService = FletX.put(
            UserService(), tag = 'user_srv'
        )
        super().__init__()

    def on_initialized(self):
        """Hook called when initializing controller"""
        print("UsersController initialized.")

    def on_ready(self):
        """Hook called when the controller is ready"""
        print("UsersController is READY!!!")
    
    def on_disposed(self):
        """Hook called when disposing controller"""
        print("UsersController is disposing")

    def all(self) -> list[UserInfo]:
        """Get All Users."""

        # Set loading state
        self.set_loading(True)
        result = []

        try:
            # Make the request
            res = self.userService.all()

            if res.ok and res.is_json:
                # Then parse ans return user list
                result = [UserInfo.from_json(user) for user in res.json()]

            # If request failed, set error message
            else:
                self.set_error(
                    get_http_error_message(res.status)
                )

        except Exception as e:
            print(f"Error fetching users: {e}")
        
        finally:
            self.set_loading(False)
            return result
        
    def retrieve(self, id: int) -> Optional[UserInfo]:
        """Retrieve user by a given id"""

        # Set loading state
        self.set_loading(True)
        user = None

        try:
            # Make the request
            res = self.userService.retrieve(id = id)

            if res.ok and res.is_json:
                # Then parse ans return user info
                user = UserInfo.from_json(res.json())

            # If request failed, set error message
            else:
                self.set_error(
                    get_http_error_message(res.status)
                )

        except Exception as e:
            print(f"Error retrieving user {id}: {e}")
            self.set_error(str(e))

        finally:
            self.set_loading(False)
            return user
        
    def create(self, user: UserInfo) -> Optional[UserInfo]:
        """Create a new user with given information."""

        # Set loading state
        self.set_loading(True)
        created_user = None

        try:
            # Make the request
            res = self.userService.create(user)

            if res.ok and res.is_json:
                # Then parse ans return created user info
                created_user = UserInfo.from_json(res.json())

            # If request failed, set error message
            else:
                self.set_error(
                    get_http_error_message(res)
                )

        except Exception as e:
            print(f"Error creating user: {e}")
            self.set_error(str(e))

        finally:
            self.set_loading(False)
            return created_user
        
    def update(self, id: int, user: UserInfo) -> Optional[UserInfo]:
        """Update user information."""

        # Set loading state
        self.set_loading(True)
        updated_user = None

        try:
            # Make the request
            res = self.userService.update(id, user)

            if res.ok and res.is_json:
                # Then parse ans return updated user info
                updated_user = UserInfo.from_json(res.json())

            # If request failed, set error message
            else:
                self.set_error(
                    get_http_error_message(res)
                )

        except Exception as e:
            print(f"Error updating user {id}: {e}")
            self.set_error(str(e))

        finally:
            self.set_loading(False)
            return updated_user
        
    def check_email(self, email: str) -> bool:
        """Check if an email is already registered."""

        # Set loading state
        self.set_loading(True)
        exists = False

        try:
            # Make the request
            res = self.userService.check_email(email)

            if res.ok and res.is_json:
                exists = res.json().get('exists', False)

            # If request failed, set error message
            else:
                self.set_error(
                    get_http_error_message(res.status)
                )

        except Exception as e:
            print(f"Error checking email {email}: {e}")
            self.set_error(str(e))

        finally:
            self.set_loading(False)
            return exists

# GLOBAL INSTANCE
FletX.put(UsersController(), tag = 'users_ctrl')
