import json
from typing import Any

from openai import OpenAI, OpenAIError
from pydantic import BaseModel, ValidationError, create_model

from .config import settings


class AIExtractionError(RuntimeError):
    pass


_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not settings.ai_enabled:
            raise AIExtractionError("OPENAI_API_KEY is not configured")
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def _build_schema(fields: list[str]) -> type[BaseModel]:
    return create_model(
        "ExtractedData",
        **{f: (str | None, None) for f in fields},  # type: ignore[arg-type]
    )


def extract_data(content: str, fields: list[str]) -> dict[str, Any]:
    """Extract structured fields from page content using OpenAI JSON mode."""
    if not fields:
        return {}

    schema_model = _build_schema(fields)
    schema_json = json.dumps(schema_model.model_json_schema(), indent=2)

    prompt = (
        "You extract structured information from web page text.\n"
        "Respond with a single JSON object matching the schema below.\n"
        "Use null for unknown fields. Do not invent data.\n\n"
        f"JSON schema:\n{schema_json}\n\n"
        f"Webpage text:\n{content[: settings.AI_MAX_INPUT_CHARS]}"
    )

    try:
        resp = _get_client().chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
    except OpenAIError as exc:
        raise AIExtractionError(f"OpenAI request failed: {exc}") from exc

    raw = resp.choices[0].message.content or "{}"
    try:
        parsed = json.loads(raw)
        validated = schema_model.model_validate(parsed)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise AIExtractionError(f"Model returned invalid JSON: {exc}") from exc

    return validated.model_dump()
