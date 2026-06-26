import os
import json
from openai import OpenAI
from .base_judge import BaseJudge
from .evaluation_utils import classify_api_error_message

class OpenAIProvider(BaseJudge):
    def __init__(self):
        try:
            from dotenv import load_dotenv  # type: ignore
            load_dotenv(override=True)
        except Exception:
            pass

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Hata: OPENAI_API_KEY bulunamadı.")
            
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o"

    def evaluate(self, question: str, bot_response: str, expected_criteria: str) -> dict:
        prompt = f"""
        Gorevin: Chatbotun yanitini, sana verilen 'Beklenen Cevap' metni ile karsilastirmak.
        Kelime eslesmesine (keywords) takilma. Botun cevabi, beklenen cevaptaki kritik bilgileri
        (telefon numarasi, saat, islem adimi vb.) farkli kelimelerle de olsa dogru ve eksiksiz veriyor mu?
        Eger anlam ayniysa yuksek puan ver.

        Soru: {question}
        Beklenen Cevap: {expected_criteria}
        Botun Cevabi: {bot_response}

        Yaniti mutlaka su JSON formatinda don:
        {{"score": int, "reasoning": "str", "status": "PASS/FAIL"}}
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={ "type": "json_object" } # OpenAI'ın JSON modu
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            msg = str(e)
            kind = classify_api_error_message(msg)
            if kind == "SISTEM_KOTA":
                return {
                    "score": 0,
                    "reasoning": "API Kota Limiti: Lütfen bir süre bekleyip tekrar deneyin (429).",
                    "status": "SISTEM_KOTA",
                }
            if kind == "SISTEM_YETKI":
                return {
                    "score": 0,
                    "reasoning": f"OpenAI yetki/anahtar: {msg}",
                    "status": "SISTEM_YETKI",
                }
            return {"score": 0, "reasoning": f"OpenAI Hatası: {msg}", "status": "FAIL"}