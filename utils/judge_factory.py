import os
from .gemini_provider import GeminiProvider
from .openai_provider import OpenAIProvider


def get_judge():
    """LLM sağlayıcı seçimi. Google GenAI SDK yalnızca GeminiProvider (utils/gemini_provider.py) içindedir."""
    llm_type = os.getenv("LLM_TYPE", "openai").strip().lower()

    if llm_type == "openai":
        try:
            return OpenAIProvider()
        except Exception as openai_error:
            print(f"UYARI: OpenAI başlatılamadı ({openai_error}). Gemini fallback deneniyor.")
            try:
                return GeminiProvider()
            except Exception as gemini_error:
                raise ValueError(
                    "OpenAI birincil sağlayıcı başlatılamadı ve Gemini fallback de başarısız oldu. "
                    f"OpenAI hata: {openai_error} | Gemini hata: {gemini_error}"
                ) from gemini_error

    if llm_type == "gemini":
        try:
            return GeminiProvider()
        except Exception as gemini_error:
            raise ValueError(f"Gemini sağlayıcısı başlatılamadı: {gemini_error}") from gemini_error

    raise ValueError(
        f"Desteklenmeyen LLM_TYPE: {llm_type}. Desteklenen değerler: 'openai', 'gemini'."
    )
