import json
from openai import OpenAI
from .config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def extract_data(content: str, fields: list[str]):
    schema = {field: "string" for field in fields}
    prompt = f"""Extract structured information from the following webpage.
Return ONLY valid JSON.

Required fields:
{json.dumps(schema, indent=2)}

Webpage:
{content[:12000]}"""
    response = client.responses.create(model="gpt-5", input=prompt)
    return json.loads(response.output_text)
