"""
LLM provider abstraction layer.

Returns provider-agnostic handles. Each handle is either:
  - A LangChain ChatOllama instance (for Ollama)
  - A dict with provider + model + client keys (for cloud providers)

All provider clients are created once at import time and reused.
"""

from __future__ import annotations

from mythos_backend.core.config import (
    ANTHROPIC_API_KEY,
    DEFAULT_ANTHROPIC_MODEL,
    DEFAULT_CRITIC_MODEL,
    DEFAULT_GENERATOR_MODEL,
    DEFAULT_GEMINI_MODEL,
    DEFAULT_GROQ_MODEL,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OPENROUTER_MODEL,
    DEFAULT_XAI_MODEL,
    GEMINI_API_KEY,
    GROQ_API_KEY,
    LLM_PROVIDER,
    OLLAMA_BASE_URL,
    OPENROUTER_API_KEY,
    XAI_API_KEY,
)


def _init_providers() -> dict[str, bool]:
    """Initialize all provider clients. Returns dict of which are available."""
    state: dict[str, bool] = {
        "ollama": True,  # Always available as fallback
        "anthropic": False,
        "openrouter": False,
        "groq": False,
        "xai": False,
        "gemini": False,
    }

    if LLM_PROVIDER == "anthropic" and ANTHROPIC_API_KEY:
        try:
            from anthropic import Anthropic
            global _ANTHROPIC_CLIENT
            _ANTHROPIC_CLIENT = Anthropic(api_key=ANTHROPIC_API_KEY)
            state["anthropic"] = True
        except ImportError:
            pass

    if LLM_PROVIDER == "openrouter" and OPENROUTER_API_KEY:
        try:
            from openai import OpenAI
            global _OPENROUTER_CLIENT
            _OPENROUTER_CLIENT = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=OPENROUTER_API_KEY,
            )
            state["openrouter"] = True
        except ImportError:
            pass

    if LLM_PROVIDER == "groq" and GROQ_API_KEY:
        try:
            from groq import Groq
            global _GROQ_CLIENT
            _GROQ_CLIENT = Groq(api_key=GROQ_API_KEY)
            state["groq"] = True
        except ImportError:
            pass

    if LLM_PROVIDER == "xai" and XAI_API_KEY:
        try:
            from openai import OpenAI
            global _XAI_CLIENT
            _XAI_CLIENT = OpenAI(
                base_url="https://api.x.ai/v1",
                api_key=XAI_API_KEY,
            )
            state["xai"] = True
        except ImportError:
            pass

    if LLM_PROVIDER == "gemini" and GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            state["gemini"] = True
        except ImportError:
            pass

    # If the configured provider isn't available, fall back to Ollama
    if LLM_PROVIDER != "ollama" and not state.get(LLM_PROVIDER, False):
        print(f"⚠ Provider '{LLM_PROVIDER}' not available, falling back to Ollama")

    return state


# Module-level client holders (initialized lazily)
_ANTHROPIC_CLIENT = None
_OPENROUTER_CLIENT = None
_GROQ_CLIENT = None
_XAI_CLIENT = None
_PROVIDER_STATE: dict[str, bool] | None = None


def get_provider_state() -> dict[str, bool]:
    """Get (and initialize if needed) the provider availability state."""
    global _PROVIDER_STATE
    if _PROVIDER_STATE is None:
        _PROVIDER_STATE = _init_providers()
    return _PROVIDER_STATE


def _active_provider() -> str:
    """Return the actual active provider name (handles fallback)."""
    state = get_provider_state()
    if LLM_PROVIDER != "ollama" and state.get(LLM_PROVIDER):
        return LLM_PROVIDER
    return "ollama"


def get_llm_for_generation(
    model: str | None = None, temperature: float = 0.7
):
    """Get LLM handle for creative generation."""
    provider = _active_provider()

    if provider == "anthropic":
        return {
            "provider": "anthropic",
            "model": model or DEFAULT_ANTHROPIC_MODEL,
            "temperature": temperature,
            "client": _ANTHROPIC_CLIENT,
        }
    elif provider == "openrouter":
        return {
            "provider": "openrouter",
            "model": model or DEFAULT_OPENROUTER_MODEL,
            "temperature": temperature,
            "client": _OPENROUTER_CLIENT,
        }
    elif provider == "groq":
        return {
            "provider": "groq",
            "model": model or DEFAULT_GROQ_MODEL,
            "temperature": temperature,
            "client": _GROQ_CLIENT,
        }
    elif provider == "xai":
        return {
            "provider": "xai",
            "model": model or DEFAULT_XAI_MODEL,
            "temperature": temperature,
            "client": _XAI_CLIENT,
        }
    elif provider == "gemini":
        return {
            "provider": "gemini",
            "model": model or DEFAULT_GEMINI_MODEL,
            "temperature": temperature,
        }
    else:
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=model or DEFAULT_GENERATOR_MODEL or DEFAULT_OLLAMA_MODEL,
            format="json",
            keep_alive="5m",
            temperature=temperature,
            base_url=OLLAMA_BASE_URL,
        )


def get_llm_for_critique(model: str | None = None, temperature: float = 0.1):
    """Get LLM handle for critique/analysis."""
    provider = _active_provider()

    if provider == "anthropic":
        return {
            "provider": "anthropic",
            "model": model or DEFAULT_ANTHROPIC_MODEL,
            "temperature": temperature,
            "client": _ANTHROPIC_CLIENT,
        }
    elif provider == "openrouter":
        return {
            "provider": "openrouter",
            "model": model or DEFAULT_OPENROUTER_MODEL,
            "temperature": temperature,
            "client": _OPENROUTER_CLIENT,
        }
    elif provider == "groq":
        return {
            "provider": "groq",
            "model": model or DEFAULT_GROQ_MODEL,
            "temperature": temperature,
            "client": _GROQ_CLIENT,
        }
    elif provider == "xai":
        return {
            "provider": "xai",
            "model": model or DEFAULT_XAI_MODEL,
            "temperature": temperature,
            "client": _XAI_CLIENT,
        }
    elif provider == "gemini":
        return {
            "provider": "gemini",
            "model": model or DEFAULT_GEMINI_MODEL,
            "temperature": temperature,
        }
    else:
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=model or DEFAULT_CRITIC_MODEL or DEFAULT_OLLAMA_MODEL,
            keep_alive="5m",
            temperature=temperature,
            base_url=OLLAMA_BASE_URL,
        )


def invoke_llm(llm, prompt: str) -> str:
    """Unified invocation for all provider types."""
    if isinstance(llm, dict):
        provider = llm.get("provider")

        if provider == "anthropic":
            response = llm["client"].messages.create(
                model=llm["model"],
                max_tokens=4096,
                temperature=llm["temperature"],
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text

        elif provider in ("openrouter", "xai"):
            response = llm["client"].chat.completions.create(
                model=llm["model"],
                max_tokens=4096,
                temperature=llm["temperature"],
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content

        elif provider == "groq":
            response = llm["client"].chat.completions.create(
                model=llm["model"],
                max_tokens=4096,
                temperature=llm["temperature"],
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content

        elif provider == "gemini":
            import google.generativeai as genai
            m = genai.GenerativeModel(llm["model"])
            response = m.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=llm["temperature"],
                    max_output_tokens=4096,
                ),
            )
            return response.text

    # Ollama (LangChain)
    out = llm.invoke(prompt)
    return getattr(out, "content", None) or str(out)
