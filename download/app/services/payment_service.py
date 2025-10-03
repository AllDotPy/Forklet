"""
Payment Controller.

This Service class is generated from a template.
"""

import json
import websockets
from fletx.core import FletXService, Reactive
# from fletx.utils import get_page

from app.models import PaymentEvent
from app.utils import get_storage


class PaymentService(FletXService):
    """Payment Service"""

    def __init__(self, *args, **kwargs):
        self.base_url = "ws://localhost:10000/ws/realtime/transaction/"

        # Init base class
        super().__init__(**kwargs)
        self.message: Reactive[PaymentEvent] = None

    def on_start(self):
        """Do stuf here on PaymentService start"""
        
        # Setup Reactivity
        self.message.listen(
            lambda: print(self.message.value),
            auto_dispose = True
        )

        # get_page().run_task(
        #     self.connect()
        # )
    
    def on_stop(self):
        """Do stuf here on PaymentService stop"""
        pass

    def get_token(self, name:str):
        """Return saved token from Client Storage"""

        tokens: dict = (
            get_storage().get('tokens') 
            if get_storage().contains_key('tokens')
            else {}
        )
        return tokens.get(name)

    async def connect(self):
        """Connect to the websockets server"""

        while True:
            try:
                async with websockets.connect(
                    self.base_url + f'?token={self.get_token('access')}'
                ) as ws:
                    #recieve loop
                    async for message in ws:
                        # data = json.loads(message)
                        self.message.value = PaymentEvent.from_json_string(message)
            
            # An Exception Occurs
            except Exception as e:
                print(e)