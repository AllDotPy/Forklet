"""
Auth Controller.

This controller class is generated from a template.

🛠️ Customization Guide:
- You can rename or extend this class as needed.
  → Example: Inherit from a different base if you use a custom controller class.
- Add your own reactive attributes using types like `RxInt`, `RxStr`, `RxBool`, etc.
- Implement methods to handle business logic, side effects, or custom events.
- Controllers can be injected into components or apps using dependency injection or manual wiring.
"""

from fletx import FletX
from fletx.core import (
    FletXController, RxInt
)
from fletx.utils import run_async, get_event_loop

from app.services import AuthService, PaymentService
from app.models import LoginInfo, UserInfo
from app.utils import get_storage, get_http_error_message

class AuthController(FletXController):
    """Auth Controller"""

    def __init__(self):
        # Defining Auth service
        self.authService: AuthService = FletX.put(
            AuthService(), tag = 'auth_srv'
        )
        self.paymentService: PaymentService = FletX.put(
            PaymentService(), tag = 'payment_srv'
        )
        super().__init__()

    def on_initialized(self):
        """Hook called when initializing controller"""
        print("AuthController initialized.")

    def on_ready(self):
        """Hook called when the controller is ready"""
        print("AuthController is READY!!!")
    
    def on_disposed(self):
        """Hook called when disposing controller"""
        print("AuthController is disposing")

    def refresh_token(self):
        """Process token refresh request"""

         # Ste Loading state
        self.set_loading(True)
        success = False

        try:
            res = self.authService.refresh_token()

            if res.ok:
                # Then save tokens
                tokens = res.json()
                get_storage().set('tokens', tokens)
                
                # set logged_in
                get_storage().set('logged_in',True)

                success =  True

            # If request failed, set error message
            else:
                self.set_error(
                    get_http_error_message(res)
                )

        # An error occurs
        except Exception as e:
            print(e)
            self.set_error(str(e))

        # Close loading state finally
        finally:
            self.set_loading(False)
            return success

    def start_payment_service_ws(self):
        """Connect Our App to the websocket server"""

        get_event_loop().create_task(self.paymentService.connect())

    def login(self, creds: LoginInfo) -> bool:
        """Process Login request."""

        # Ste Loading state
        self.set_loading(True)
        success = False

        try:
            res = self.authService.login(creds)

            if res.ok:
                # Then save tokens
                dta = res.json()
                tokens = {
                    'access': dta.get('access_token'),
                    'refresh': dta.get('refresh_token')
                }
                get_storage().set('tokens', tokens)

                # Save user to global context
                self.set_global_context(
                    'user', UserInfo.from_json(dta.get('user', {}))
                )
                
                # set logged_in
                get_storage().set('logged_in',True)

                success =  True

                # Start ws connection
                self.start_payment_service_ws()

            # If request failed, set error message
            else:
                self.set_error(
                    get_http_error_message(res)
                )

        # An error occurs
        except Exception as e:
            print(e)
            self.set_error(str(e))

        # Close loading state finally
        finally:
            self.set_loading(False)
            return success
        
    def register(self, user: UserInfo) -> bool:
        """Register a new user."""

        # Ste Loading state
        self.set_loading(True)
        success = False

        try:
            res = self.authService.register(user)

            if res.ok:
                # Then save tokens
                dta = res.json()
                tokens = {
                    'access': dta.get('access_token'),
                    'refresh': dta.get('refresh_token')
                }
                get_storage().set('tokens', tokens)

                # Save user to global context
                self.set_global_context(
                    'user', UserInfo.from_json(dta.get('user', {}))
                )
                
                # set logged_in
                get_storage().set('logged_in',True)

                success =  True

                # Start ws connection
                self.start_payment_service_ws()

            # If request failed, set error message
            else:
                self.set_error(
                    get_http_error_message(res)
                )

        # An error occurs
        except Exception as e:
            print(e)
            self.set_error(str(e))

        # Close loading state finally
        finally:
            self.set_loading(False)
            return success
        
    def get_profile(self):
        """Retrieve current user profile."""

        # Ste Loading state
        self.set_loading(True)
        success = False

        try:
            res = self.authService.get_profile()

            if res.ok:
                # Then save tokens
                user = UserInfo.from_json(res.json())
                
                # Save user to global context
                self.set_global_context('user',user)

                success =  True

            # If request failed, set error message
            else:
                self.set_error(
                    get_http_error_message(res)
                )

        # An error occurs
        except Exception as e:
            print(e)
            self.set_error(str(e))

        # Close loading state finally
        finally:
            self.set_loading(False)
            return success

# GLOBAL INSTANCE
FletX.put(AuthController(), tag = 'auth_ctrl')
