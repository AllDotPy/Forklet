"""
This widegt will comme with the V.0.1.5.X versions of FletX.
But for now we need it here, so i'll copy-past it to use it derictly.
"""

from flet import *
from typing import List, Optional, Union, Callable
from enum import Enum


####
##      STEP STATE CHOICES
#####
class StepState(Enum):
    """Available state for a step."""

    DISABLED = "disabled"
    INACTIVE = "inactive"
    ACTIVE = "active"
    COMPLETED = "completed"
    ERROR = "error"


####
##      STEPPER ORIENTATION CHOICES
#####
class StepperOrientation(Enum):
    """Stepper Orientation"""

    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


####
##      A STEP REPRESENTATION
#####
class Step:
    """A Step Representation"""

    def __init__(
        self,
        title: str,
        content: Optional[Union[str, Control]] = None,
        icon: Optional[Union[str, Icon, Image, Control]] = None,
        state: StepState = StepState.INACTIVE,
        is_active: bool = False,
        subtitle: Optional[str] = None
    ):
        self.title = title
        self.content = content
        self.icon = icon
        self.state = state
        self.is_active = is_active
        self.subtitle = subtitle


####
##      STEPPER WIDGET
#####
class Stepper(Container):
    """Stepper Widget"""
    
    def __init__(
        self,
        steps: List[Step],
        current_step: int = 0,
        orientation: StepperOrientation = StepperOrientation.HORIZONTAL,

        # Colors
        active_color: str = Colors.BLUE,
        completed_color: str = Colors.GREEN,
        inactive_color: str = Colors.GREY_400,
        error_color: str = Colors.RED,
        disabled_color: str = Colors.GREY_300,

        # Styles
        connector: Control = None,
        connector_thickness: float = 2,
        connector_size: float = 50,
        step_size: float = 32,
        title_style: TextStyle = None,
        subtitle_style: TextStyle = None,
        # indicator: Control = None,

        # Callbacks
        on_step_tapped: Optional[Callable[[int], None]] = None,
        on_step_changed: Optional[Callable[[int], None]] = None,

        # Display Options
        show_step_numbers: bool = True,
        show_titles: bool = True,
        show_subtitles: bool = True,
        show_step_circle: bool = True,
        clickable_steps: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.steps = steps
        self.current_step = current_step
        self.orientation = orientation
        
        # Colors
        self.active_color = active_color
        self.completed_color = completed_color
        self.inactive_color = inactive_color
        self.error_color = error_color
        self.disabled_color = disabled_color
        
        # Styles
        self.connector = connector
        self.connector_thickness = connector_thickness
        self.connector_size = connector_size
        self.step_size = step_size
        self.title_style = title_style
        self.subtitle_style = subtitle_style
        # self.step_circle_size = step_circle_size
        
        # Callbacks
        self.on_step_tapped = on_step_tapped
        self.on_step_changed = on_step_changed
        
        # Display Options
        self.show_step_numbers = show_step_numbers
        self.show_titles = show_titles
        self.show_subtitles = show_subtitles
        self.show_step_circle = show_step_circle
        self.clickable_steps = clickable_steps
        
        # Setup Initial States
        self._update_step_states()

        self.content = self.build() 

    def _get_step_color(self, step: Step, index: int) -> str:
        """Return appropriated step color based on state"""

        # Disabled
        if step.state == StepState.DISABLED:
            return self.disabled_color
        
        # Error
        elif step.state == StepState.ERROR:
            return self.error_color
        
        # Completed
        elif step.state == StepState.COMPLETED or index < self.current_step:
            return self.completed_color
        
        # Current Step
        elif index == self.current_step:
            return self.active_color
        
        else:
            return self.inactive_color

    def _create_step_icon(self, step: Step, index: int) -> Control:
        """Creates a given step Icon widget"""

        color = self._get_step_color(step, index)
        
        # Use custom icon if provided
        if step.icon:
            if isinstance(step.icon, str):
                return Icon(step.icon, color=color, size=self.step_size * 0.6)
            elif isinstance(step.icon, Control):
                return step.icon
            else:
                return step.icon
        
        # State Icons
        if step.state == StepState.COMPLETED or index < self.current_step:
            icon_name = Icons.CHECK
        
        # Error Icon
        elif step.state == StepState.ERROR:
            icon_name = Icons.ERROR
        else:
            # Show Step Number if enabled
            if self.show_step_numbers:
                return Text(
                    str(index + 1),
                    color = Colors.WHITE if index == self.current_step else color,
                    weight = FontWeight.BOLD,
                    size = self.step_size * 0.4
                )
            else:
                icon_name = Icons.CIRCLE

        return Icon(
            icon_name,
            color = Colors.WHITE if index == self.current_step else color,
            size = self.step_size * 0.8
        )

    def _create_step_circle(self, step: Step, index: int) -> Control:
        """Create Step Circle"""

        # Get color and icon
        color = self._get_step_color(step, index)
        icon = self._create_step_icon(step, index)
        
        circle = Container(
            content = icon,
            width = self.step_size,
            height = self.step_size,
            bgcolor = (
                color 
                if (index == self.current_step and self.show_step_circle) 
                else Colors.TRANSPARENT
            ),
            border = border.all(2, color) if self.show_step_circle else None,
            border_radius = self.step_size / 2,
            alignment = alignment.center,
        )
        
        # Setup tap Event
        if self.clickable_steps and step.state != StepState.DISABLED:
            circle = GestureDetector(
                content = circle,
                on_tap = lambda e, i = index: self._on_step_tap(i)
            )
        
        return circle

    def _create_connector(self, is_completed: bool = False) -> Control:
        """Create connector for steps"""

        color = self.completed_color if is_completed else self.inactive_color
        
        # Custom connector provided
        if self.connector:
            return self.connector
        
        # Use default Connector
        if self.orientation == StepperOrientation.HORIZONTAL:
            return Container(
                width = self.connector_size,
                height = self.connector_thickness,
                bgcolor = color,
                margin = margin.symmetric(horizontal=5)
            )
        else:
            return Container(
                width = self.connector_thickness,
                height = self.connector_size,
                bgcolor = color,
                margin = margin.symmetric(vertical=5)
            )

    def _create_step_content(self, step: Step, index: int) -> Control:
        """Create a step content (title, subtitle)"""

        controls = []
        
        # Show title if needed
        if self.show_titles and step.title:
            color = self._get_step_color(step, index)
            title = Text(
                step.title,
                weight = FontWeight.BOLD if index == self.current_step else FontWeight.NORMAL,
                style = self.title_style,
                # color = color,
                # size = 14
            )
            controls.append(title)
        
        # Show subtitle if needed
        if self.show_subtitles and step.subtitle:
            subtitle = Text(
                step.subtitle,
                style = self.subtitle_style,
                # color = Colors.GREY_600,
                # size = 12
            )
            controls.append(subtitle)
        
        # Custom step content
        if step.content and index == self.current_step:
            if isinstance(step.content, str):
                content_widget = Text(step.content)
            else:
                content_widget = step.content
            controls.append(
                Container(
                    content = content_widget, 
                    margin = margin.only(top=10))
                )
        
        if not controls:
            return Container()
        
        return Column(
            controls = controls,
            spacing = 2,
            horizontal_alignment = (
                CrossAxisAlignment.CENTER 
                if self.orientation == StepperOrientation.HORIZONTAL 
                else CrossAxisAlignment.START
            )
        )

    def _on_step_tap(self, index: int):
        """Step Tap event manager"""

        if self.on_step_tapped:
            self.on_step_tapped(index)
        
        # Change active step if allowed
        if self.steps[index].state != StepState.DISABLED:
            old_step = self.current_step
            self.current_step = index
            self._update_step_states()
            self.update()
            
            if self.on_step_changed and old_step != index:
                self.on_step_changed(index)

    def _update_step_states(self):
        """Update steps"""

        for i, step in enumerate(self.steps):
            if step.state != StepState.DISABLED and step.state != StepState.ERROR:
                if i < self.current_step:
                    step.state = StepState.COMPLETED
                elif i == self.current_step:
                    step.state = StepState.ACTIVE
                else:
                    step.state = StepState.INACTIVE

    def build(self):
        """Build Stepper Widget"""
        step_widgets = []
        
        for i, step in enumerate(self.steps):
            step_circle = self._create_step_circle(step, i)
            step_content = self._create_step_content(step, i)
            
            if self.orientation == StepperOrientation.HORIZONTAL:
                step_widget = Column(
                    spacing = 8,
                    horizontal_alignment = CrossAxisAlignment.CENTER, 
                    controls = [
                        step_circle,
                        step_content
                    ], 
                )
            else:
                step_widget = Row(
                    controls = [
                        step_circle,
                        Container(
                            step_content, 
                            margin = margin.only(left=15)
                        )
                    ], 
                    alignment = MainAxisAlignment.START, 
                    spacing = 0
                )
            
            step_widgets.append(step_widget)
            
            # Add step connector
            if i < len(self.steps) - 1:
                is_completed = i < self.current_step
                connector = self._create_connector(is_completed)
                step_widgets.append(connector)
        
        if self.orientation == StepperOrientation.HORIZONTAL:
            return Row(
                spacing = 0,
                expand = True,
                controls = step_widgets,
                alignment = MainAxisAlignment.CENTER,
                vertical_alignment = CrossAxisAlignment.CENTER
            )
        else:
            return Column(
                spacing = 0,
                expand = True,
                controls = step_widgets,
                alignment = MainAxisAlignment.START,
                horizontal_alignment = CrossAxisAlignment.CENTER,
            )

    # Public methods
    def next_step(self):
        """Go to the nex stepe"""

        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self._update_step_states()
            self.update()
            if self.on_step_changed:
                self.on_step_changed(self.current_step)

    def previous_step(self):
        """Rreturn to previous step"""

        if self.current_step > 0:
            self.current_step -= 1
            self._update_step_states()
            self.update()
            if self.on_step_changed:
                self.on_step_changed(self.current_step)

    def go_to_step(self, step_index: int):
        """Jump to a specific step."""

        if 0 <= step_index < len(self.steps) and self.steps[step_index].state != StepState.DISABLED:
            old_step = self.current_step
            self.current_step = step_index
            self._update_step_states()
            self.update()
            if self.on_step_changed and old_step != step_index:
                self.on_step_changed(step_index)

    def set_step_state(self, step_index: int, state: StepState):
        """Change step State"""

        if 0 <= step_index < len(self.steps):
            self.steps[step_index].state = state
            self.update()

    def reset(self):
        """Reset the stepper"""

        self.current_step = 0
        for step in self.steps:
            if step.state not in [StepState.DISABLED, StepState.ERROR]:
                step.state = StepState.INACTIVE
        self._update_step_states()
        self.update()