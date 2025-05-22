from openai import OpenAI
from config.config import OPENAI_API_KEY, SUMMARY_OPENAI_MODEL, SUMMARY_OPENAI_TEMPERATURE
from config.summary_promt import SUMMARY_PROMPT


class SummaryService:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = SUMMARY_OPENAI_MODEL

    def create_summary(self, messages: list, previous_summary: str = "") -> str:
        """Создает саммари из истории сообщений с учетом предыдущего саммари"""
        # Формируем контекст с учетом предыдущего саммари
        context = ""
        if previous_summary:
            context = f"Предыдущий контекст диалога: {previous_summary}\n\n"
        
        summary_prompt = [
            {"role": "system", "content": SUMMARY_PROMPT},
            {"role": "user", "content": f"{context}Вот новая история диалога:\n" + "\n".join([f"{msg.role}: {msg.content}" for msg in messages])}
        ]
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=summary_prompt,
            temperature=SUMMARY_OPENAI_TEMPERATURE
        )
        return response.choices[0].message.content 