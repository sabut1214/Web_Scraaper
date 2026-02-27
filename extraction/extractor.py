import json
import re
from typing import Dict, Any, Optional
from config import get_settings
from extraction.cleaner import html_cleaner
from extraction.prompts import (
    get_extraction_system_prompt,
    get_extraction_user_prompt,
    build_error_recovery_prompt,
)
from core.logger import setup_logger

logger = setup_logger("llm_extractor")


class LLMExtractor:
    def __init__(self):
        self.settings = get_settings()
        self._client = None

    def _get_client(self):
        if self._client is None:
            provider = self.settings.extraction_provider
            
            if provider == "openai":
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.settings.openai_api_key)
            elif provider == "anthropic":
                import anthropic
                self._client = anthropic.AsyncAnthropic(api_key=self.settings.anthropic_api_key)
            elif provider == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=self.settings.gemini_api_key)
                self._client = genai
            else:
                raise ValueError(f"Unknown provider: {provider}")
        
        return self._client

    async def extract(
        self,
        html: str,
        schema: Dict[str, Any],
        custom_prompt: Optional[str] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        cleaned_html = html_cleaner.clean_for_extraction(
            html,
            max_length=4000
        )
        
        system_prompt = get_extraction_system_prompt()
        user_prompt = get_extraction_user_prompt(
            cleaned_html,
            schema,
            custom_prompt,
        )
        
        for attempt in range(max_retries):
            try:
                result = await self._call_llm(system_prompt, user_prompt)
                
                parsed = self._parse_json_response(result)
                
                validated = self._validate_against_schema(parsed, schema)
                
                return validated
                
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error (attempt {attempt + 1}): {e}")
                user_prompt = build_error_recovery_prompt(
                    str(e),
                    result if 'result' in locals() else "",
                    schema,
                )
            except Exception as e:
                logger.error(f"Extraction error (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    raise
        
        return {}

    async def _call_llm(self, system: str, user: str) -> str:
        client = self._get_client()
        provider = self.settings.extraction_provider
        
        if provider == "openai":
            response = await client.chat.completions.create(
                model=self.settings.extraction_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=self.settings.extraction_temperature,
                max_tokens=self.settings.extraction_max_tokens,
            )
            return response.choices[0].message.content
        
        elif provider == "anthropic":
            response = await client.messages.create(
                model=self.settings.extraction_model,
                system=system,
                messages=[{"role": "user", "content": user}],
                temperature=self.settings.extraction_temperature,
                max_tokens=self.settings.extraction_max_tokens,
            )
            return response.content[0].text
        
        elif provider == "gemini":
            model = client.GenerativeModel(self.settings.extraction_model)
            response = await model.generate_content(
                f"{system}\n\n{user}",
                generation_config={
                    "temperature": self.settings.extraction_temperature,
                    "max_output_tokens": self.settings.extraction_max_tokens,
                },
            )
            return response.text
        
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        response = response.strip()
        
        json_match = re.search(r"\{[\s\S]*\}|\[[\s\S]*\]", response)
        if json_match:
            response = json_match.group()
        
        return json.loads(response)

    def _validate_against_schema(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Any],
    ) -> Dict[str, Any]:
        if "properties" in schema:
            result = {}
            for key, field_schema in schema["properties"].items():
                if key in data:
                    result[key] = self._validate_field(data[key], field_schema)
            return result
        
        return data

    def _validate_field(self, value: Any, field_schema: Dict[str, Any]) -> Any:
        field_type = field_schema.get("type")
        
        if value is None:
            return None
        
        if field_type == "object" and "properties" in field_schema:
            if isinstance(value, dict):
                return self._validate_against_schema(value, field_schema)
        
        elif field_type == "array" and "items" in field_schema:
            if isinstance(value, list):
                return [
                    self._validate_field(item, field_schema["items"])
                    for item in value
                ]
        
        return value


llm_extractor = LLMExtractor()


async def extract_structured_data(
    html: str,
    schema: Dict[str, Any],
    prompt: Optional[str] = None,
) -> Dict[str, Any]:
    return await llm_extractor.extract(
        html=html,
        schema=schema,
        custom_prompt=prompt,
    )
