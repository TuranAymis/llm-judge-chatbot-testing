import os
import json
import re
import time
from typing import Any

from google import genai

from .base_judge import BaseJudge
from .evaluation_utils import classify_api_error_message


class GeminiProvider(BaseJudge):
    def __init__(self) -> None:
        try:
            from dotenv import load_dotenv  # type: ignore
            load_dotenv(override=True)
        except Exception:
            pass

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Hata: GEMINI_API_KEY bulunamadı. Lütfen .env dosyanızı kontrol edin.")

        self._client: genai.Client = genai.Client(api_key=api_key)
        self.model_candidates = ["gemini-1.5-flash", "gemini-2.0-flash"]
        self._max_retries = 3

    @staticmethod
    def _extract_retry_seconds(msg: str) -> float:
        match = re.search(r"Please retry in\s*([0-9]+(?:\.[0-9]+)?)s", msg, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return 5.0
        return 5.0

    @staticmethod
    def _response_text(response: Any) -> str:
        text = getattr(response, "text", None)
        return (text or "").strip()

    def evaluate(self, question: str, bot_response: str, expected_criteria: str) -> dict:
        prompt = f"""
        Görevin: Chatbotun yanıtını, sana verilen 'Beklenen Cevap' metni ile karşılaştırmak.
        Kelime eşleşmesine (keywords) takılma. Botun cevabı, beklenen cevaptaki kritik bilgileri
        (telefon numarası, saat, işlem adımı vb.) farklı kelimelerle de olsa doğru ve eksiksiz veriyor mu?
        Eğer anlam aynıysa yüksek puan ver.

        Soru: {question}
        Beklenen Cevap: {expected_criteria}
        Botun Cevabı: {bot_response}

        Yanıtı mutlaka şu JSON formatında dön:
        {{"score": int, "reasoning": "str", "status": "PASS/FAIL"}}
        """

        last_error = ""
        for model_name in self.model_candidates:
            attempt = 0
            while attempt <= self._max_retries:
                try:
                    response = self._client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                    raw_text = self._response_text(response).replace("```json", "").replace("```", "").strip()
                    if not raw_text:
                        raise ValueError("Gemini yanıtı boş.")
                    return json.loads(raw_text)
                except Exception as e:
                    msg = str(e)
                    last_error = msg
                    kind = classify_api_error_message(msg)

                    if "not found" in msg.lower() and "model" in msg.lower():
                        break

                    if kind == "SISTEM_YETKI":
                        return {
                            "score": 0,
                            "reasoning": "Gemini API Yetki Hatası (401/403). Lütfen API anahtarını kontrol edin.",
                            "status": "SISTEM_YETKI",
                        }

                    if kind == "SISTEM_KOTA":
                        retry_seconds = self._extract_retry_seconds(msg)
                        if attempt >= self._max_retries:
                            return {
                                "score": 0,
                                "reasoning": "API Kota Limiti: Lütfen bir süre bekleyip tekrar deneyin (429).",
                                "status": "SISTEM_KOTA",
                            }
                        time.sleep(max(retry_seconds, 0.0))
                        attempt += 1
                        continue

                    return {
                        "score": 0,
                        "reasoning": "Gemini API Hatası. Lütfen bağlantı ve model ayarlarını kontrol edin.",
                        "status": "FAIL",
                    }

        if classify_api_error_message(last_error) == "SISTEM_KOTA":
            return {
                "score": 0,
                "reasoning": "API Kota Limiti: Lütfen bir süre bekleyip tekrar deneyin (429).",
                "status": "SISTEM_KOTA",
            }
        return {
            "score": 0,
            "reasoning": "Gemini API Hatası. Lütfen bağlantı ve model ayarlarını kontrol edin.",
            "status": "FAIL",
        }
