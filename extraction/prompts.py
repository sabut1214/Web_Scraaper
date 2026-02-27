from typing import Dict, Any, Optional
import json


def get_extraction_system_prompt() -> str:
    return """You are an expert data extraction system. Your task is to extract structured data from web page content.

You must:
1. Analyze the provided HTML/Text content
2. Extract information matching the user's schema
3. Return valid JSON that strictly follows the schema
4. Handle missing or ambiguous data gracefully

Return ONLY valid JSON - no explanations, no markdown, no additional text."""


def get_extraction_user_prompt(
    html: str,
    schema: Dict[str, Any],
    custom_prompt: Optional[str] = None,
) -> str:
    schema_json = json.dumps(schema, indent=2)
    
    prompt = f"""Extract structured data from the following web page content.

SCHEMA:
```json
{schema_json}
```

"""
    
    if custom_prompt:
        prompt += f"""USER INSTRUCTIONS:
{custom_prompt}

"""

    prompt += f"""WEB PAGE CONTENT:
{html}

Return JSON matching the schema:"""
    
    return prompt


def get_schema_from_field(field: Dict[str, Any]) -> str:
    field_type = field.get("type", "string")
    description = field.get("description", "")
    required = field.get("required", False)
    
    base = f"- {field['name']} ({field_type})"
    if description:
        base += f": {description}"
    if required:
        base += " [REQUIRED]"
    else:
        base += " [optional]"
    
    if field_type == "object" and "properties" in field:
        base += "\n  Properties:"
        for prop in field["properties"].values():
            base += "\n    " + get_schema_from_field(prop).replace("\n", "\n    ")
    
    if field_type == "array" and "items" in field:
        base += "\n  Items:"
        base += "\n    " + get_schema_from_field(field["items"]).replace("\n", "\n    ")
    
    return base


def build_error_recovery_prompt(
    original_error: str,
    last_output: str,
    schema: Dict[str, Any],
) -> str:
    schema_json = json.dumps(schema, indent=2)
    
    return f"""The previous extraction failed with this error: {original_error}

The previous output was:
{last_output}

Please fix the JSON and ensure it matches this schema:
```json
{schema_json}
```

Return ONLY valid JSON:"""
