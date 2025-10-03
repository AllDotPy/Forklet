from flet import *
from fletx.core import (
    FletXPage
)
from fletx.widgets import Obx

from ..controllers.counter import CounterController


class CounterPage(FletXPage):

    def __init__(self):
        self.ctrl = CounterController()

        super().__init__(
            bgcolor = Theme.scaffold_bgcolor
        )
    
    def build(self):
        return Column(
            spacing = 10,
            expand = True,
            alignment = MainAxisAlignment.CENTER,
            horizontal_alignment = CrossAxisAlignment.CENTER,
            controls = [
                Container(
                    height = 100
                ),
                Image(
                    src = 'logo.png',
                    fit = ImageFit.CONTAIN,
                    width = 120,
                    height = 120
                ),
                Text('🚀 powered by FletX 0.1.4.a2',color = Colors.GREY_600),
                Text('Python version 3.12', color = Colors.GREY_600),
                Container(
                    expand = True,
                    alignment = alignment.center,
                    content = Column(
                        alignment = MainAxisAlignment.CENTER,
                        horizontal_alignment = CrossAxisAlignment.CENTER,
                        controls = [
                            Text(
                                "Fakeshop Counter",
                                size = 20,
                                weight = FontWeight.BOLD
                            ),
                            Obx(
                                builder_fn = lambda: Text(
                                    value = f'{self.ctrl.count}',
                                    size = 100, 
                                    weight = FontWeight.BOLD
                                )
                            ),
                            ElevatedButton(
                                "Increment",
                                on_click=lambda e: self.ctrl.count.increment()  # Auto UI update
                            )
                        ]
                    )
                ),
                Container(
                    height = 100,
                    content = Text('Thanks for choosing FletX'),
                ),
            ]
        )