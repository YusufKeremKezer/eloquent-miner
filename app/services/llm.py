from openai import OpenAI

from app.core.config import settings


def get_llm_client() -> OpenAI:
    """Returns an OpenAI-compatible client based on the configured provider."""

    if settings.llm_provider in ["openai", "groq","gemini","openrouter"]:
        if not settings.llm_api_key:
            raise ValueError(f"LLM_API_KEY is required for provider: {settings.llm_provider}")
        return OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url or None
        )
        
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")

def call_llm(system_prompt: str, user_prompt: str) -> str:
    """Calls the LLM and returns the raw string response."""
    client = get_llm_client()
    
    # We use response_format for JSON if the model supports it. 
    # Deepseek models on OpenRouter generally support this well.
    kwargs = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2
    }
    
    # Some open-source models on OpenRouter crash if you force json_object.
    # We add it safely for known good providers, or rely on the prompt.
    if settings.llm_provider in ["openai", "openrouter"]:
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
    
    return response.choices[0].message.content