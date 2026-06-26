from abc import ABC, abstractmethod

class BaseJudge(ABC):
    """
    Tüm LLM sağlayıcıları (Gemini, OpenAI, Ollama vb.) 
    bu sınıftan türemeli ve 'evaluate' metodunu uygulamalıdır.
    """

    @abstractmethod
    def evaluate(self, question: str, bot_response: str, expected_criteria: str) -> dict:
        """
        Bu metod, chatbot yanıtını değerlendirir.
        
        Args:
            question: Kullanıcının sorduğu soru.
            bot_response: Chatbot'un verdiği ham yanıt.
            expected_criteria: Test verisindeki beklenen mantık veya keywordler.

        Returns:
            dict: {"score": int, "reasoning": str, "status": str} formatında bir sonuç.
        """
        pass