import ollama

from app.config.settings import settings


class AIService:

    def generate(
        self,
        prompt: str,
        system: str = "",
    ):

        messages = []

        if system:
            messages.append({
                "role": "system",
                "content": system,
            })

        messages.append({
            "role": "user",
            "content": prompt,
        })

        response = ollama.chat(
            model=settings.OLLAMA_MODEL,
            messages=messages,
        )

        return response["message"]["content"]


ai_service = AIService()