import datetime
from typing import (
    Dict, Any, TypeVar, Type, Union, List, 
    get_origin, get_args
)
from dataclasses import (
    dataclass, asdict, fields, is_dataclass
)
import json

T = TypeVar('T', bound='BaseModel')


####
##      BASE MODEL CLASS
#####
@dataclass
class BaseModel:
    ''' Base class for all models. '''
    
    def to_json(self) -> Dict[str, Any]:
        """
        Converts model fields into a dictionary.
        """

        def convert_value(value):
            # Date
            if isinstance(value, datetime.date):
                return str(value)
            
            # Model objects
            elif isinstance(value, BaseModel):
                return value.to_json()
            
            # Lists
            elif isinstance(value, list):
                return [convert_value(item) for item in value]
            return value

        return {
            k: convert_value(v)
            for k, v in asdict(self).items()
            if v is not None
        }
    
    def to_json_string(self) -> str:
        """
        Converts model fields into a JSON string.
        """
        return json.dumps(self.to_json())
    
    @classmethod
    def from_json(cls: Type[T], json_dict: Dict[str, Any]) -> T:
        """
        Loads model from a dictionary.
        """
        if json_dict is None:
            return None

        field_types = {f.name: f.type for f in fields(cls)}
        init_kwargs = {}
        
        for field_name, field_type in field_types.items():
            if field_name not in json_dict:
                continue
                
            value = json_dict[field_name]
            if value is None:
                init_kwargs[field_name] = None
                continue
                
            # Handle Optional/Union types
            if get_origin(field_type) is Union:
                field_type = [t for t in get_args(field_type) if t is not type(None)][0]  # noqa: E721
            
            # Handle list of models
            if get_origin(field_type) is list or get_origin(field_type) is List:
                item_type = get_args(field_type)[0]
                if is_dataclass(item_type) and issubclass(item_type, BaseModel):
                    init_kwargs[field_name] = [item_type.from_json(item) for item in value]
                else:
                    init_kwargs[field_name] = [item_type(item) for item in value]
            
            # Handle nested models
            elif is_dataclass(field_type) and issubclass(field_type, BaseModel):
                init_kwargs[field_name] = field_type.from_json(value)
            
            # Handle datetime
            elif (
                field_type 
                in (datetime.date, datetime.datetime) 
                and isinstance(value, str)
            ):
                if field_type == datetime.date:
                    init_kwargs[field_name] = datetime.date.fromisoformat(value)
                else:  # field_type == datetime.datetime
                    init_kwargs[field_name] = datetime.datetime.fromisoformat(value)
            
            # Handle simple types
            else:
                try:
                    init_kwargs[field_name] = field_type(value)
                except (TypeError, ValueError):
                    init_kwargs[field_name] = value
        
        return cls(**init_kwargs)
    
    @classmethod
    def from_json_string(cls: Type[T], json_str: str) -> T:
        """
        Loads model from a JSON string.
        """
        json_dict = json.loads(json_str)
        return cls.from_json(json_dict)
    
    def __str__(self):
        return f"{self.__class__.__name__} {self.to_json()}"
    
    def __repr__(self):
        return self.__str__()
