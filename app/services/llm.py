from openai import OpenAI
from app.core.config import settings

def get_llm_client() -> OpenAI:
    """Returns an OpenAI-compatible client based on the configured provider."""
    
    if settings.llm_provider == "openrouter":
        api_key = settings.openrouter_api_key or settings.llm_api_key
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is required for OpenRouter.")
            
        return OpenAI(
            base_url=settings.openrouter_base_url,
            api_key=api_key,
            # OpenRouter requires these headers to identify the app
            default_headers={
                "HTTP-Referer": settings.openrouter_app_url,
                "X-Title": settings.app_name,
            }
        )
        
    elif settings.llm_provider == "ollama":
        return OpenAI(
            base_url=settings.llm_base_url or "http://localhost:11434/v1",
            api_key=settings.llm_api_key or "ollama"
        )
        
    elif settings.llm_provider in ["openai", "groq"]:
        if not settings.llm_api_key:
            raise ValueError(f"LLM_API_KEY is required for provider: {settings.llm_provider}")
        return OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url or None
        )
        
    elif settings.llm_provider == "manual":
        raise ValueError("LLM_PROVIDER is set to 'manual'. Change it in .env to use automated extraction.")
        
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