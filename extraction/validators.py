from typing import Any, Dict
from pydantic import BaseModel, ValidationError, create_model
from core.logger import setup_logger

logger = setup_logger("validators")


class OutputValidator:
    @staticmethod
    def validate_json(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        try:
            properties = schema.get("properties", {})
            
            for key, field_def in properties.items():
                if key not in data:
                    if field_def.get("required", False):
                        logger.warning(f"Missing required field: {key}")
                        return False
                    continue
                
                if not OutputValidator._validate_type(
                    data[key],
                    field_def
                ):
                    logger.warning(f"Invalid type for field {key}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False

    @staticmethod
    def _validate_type(value: Any, field_def: Dict[str, Any]) -> bool:
        field_type = field_def.get("type")
        
        if value is None:
            return True
        
        if field_type == "string":
            return isinstance(value, str)
        
        elif field_type == "number":
            return isinstance(value, (int, float))
        
        elif field_type == "integer":
            return isinstance(value, int)
        
        elif field_type == "boolean":
            return isinstance(value, bool)
        
        elif field_type == "array":
            if not isinstance(value, list):
                return False
            if "items" in field_def:
                return all(
                    OutputValidator._validate_type(item, field_def["items"])
                    for item in value
                )
            return True
        
        elif field_type == "object":
            if not isinstance(value, dict):
                return False
            if "properties" in field_def:
                return all(
                    OutputValidator._validate_type(
                        value.get(key),
                        field_def
                    )
                    for key, field_def in field_def["properties"].items()
                )
            return True
        
        return True

    @staticmethod
    def create_pydantic_model(schema: Dict[str, Any], model_name: str = "DynamicModel"):
        properties = {}
        
        for key, field_def in schema.get("properties", {}).items():
            field_type = field_def.get("type", "string")
            
            if field_type == "string":
                pydantic_type = str
            elif field_type == "number":
                pydantic_type = float
            elif field_type == "integer":
                pydantic_type = int
            elif field_type == "boolean":
                pydantic_type = bool
            elif field_type == "object":
                pydantic_type = dict
            elif field_type == "array":
                pydantic_type = list
            else:
                pydantic_type = Any
            
            default = ... if field_def.get("required", False) else None
            properties[key] = (pydantic_type, default)
        
        return create_model(model_name, **properties)


output_validator = OutputValidator()
