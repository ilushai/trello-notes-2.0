# services/llm_service.py

import openai
import json
import logging
from my_config import OPENAI_API_KEY

# Инициализируем клиент OpenAI с вашим ключом
client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)

# Системный промпт, который объясняет модели ее задачу
SYSTEM_PROMPT = """
You are an expert task classifier for a Trello board. Your goal is to analyze the user's note and return a JSON object with the most appropriate list and label.

Your response MUST be ONLY a valid JSON object with two keys: "list" and "label". Do not add any other text or explanations.

Here are the available lists and labels with detailed descriptions of what should go where:

AVAILABLE LISTS:
1.  "Tasks": For concrete tasks, work, professional development, and technical topics.
    -   Content: Poker analysis, work projects, study notes, AI/ML research, crypto trading strategies, technical tasks, learning new skills.
    -   Examples: "Проанализировать вчерашнюю покерную сессию", "Изучить новую архитектуру нейросети", "Купить BTC на просадке".

2.  "Ideas": For creative thoughts, personal reflections, abstract concepts, and quotes.
    -   Content: Philosophical ideas, personal insights, interesting quotes, reflections on life, non-work-related creative concepts. THIS IS NOT for work notes like poker strategy.
    -   Examples: "Мысль о том, как важно быть благодарным", "Цитата Сенеки о времени", "Идея для нового рассказа".

3.  "Chores": For everyday household tasks, errands, and as a FALLBACK for any note that does not clearly fit into "Tasks" or "Ideas".
    -   Content: Shopping lists, reminders to fix something at home, appointments. If you are unsure where a note belongs, place it here.
    -   Examples: "Купить соль и молоко", "Записаться к врачу", "Починить кран".

AVAILABLE LABELS:
-   "poker": For anything related to poker (strategy, session notes, learning).
-   "ai": For notes about artificial intelligence, machine learning, neural networks.
-   "crypto": For cryptocurrencies, blockchain, trading.
-   "health": For notes about physical or mental health, medicine, sports.
-   "art": For art, creativity, music, literature.
-   "networking": Use this for general quotes or thoughts about communication, social interaction, or personal relationships that don't fit a more specific category.
-   "notes": A general label for miscellaneous thoughts, ideas, or tasks that do not fit any other label.

PROCESSING LOGIC:
1.  First, determine the correct LIST based on its core purpose (Work/Tech vs. Creative/Reflection vs. Household/Fallback).
2.  Second, choose the most specific LABEL for the note's content.
3.  Special Rule for Quotes: If a note is a quote, first check its topic. A psychological quote should be "health". An art quote should be "art". If a quote is on a general or social topic, use "networking".
4.  Strictly adhere to the list and label names provided.

Now, analyze the following user note and provide your JSON response.
"""

async def get_trello_details(text: str) -> dict:
    """
    Получает от OpenAI имя списка и метки для Trello на основе текста заметки.
    """
    try:
        logging.info(f"Отправка текста в OpenAI для анализа: {text[:30]}...")
        
        response = await client.chat.completions.create(
            model="gpt-4o",  # Рекомендую gpt-4o для лучшего следования инструкциям
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            response_format={"type": "json_object"},
            temperature=0.2, # Низкая температура для более предсказуемого результата
        )
        
        result_content = response.choices[0].message.content
        details = json.loads(result_content)
        
        logging.info(f"OpenAI вернул: {details}")
        return details

    except Exception as e:
        logging.error(f"Ошибка при обращении к OpenAI: {e}")
        # Возвращаем "безопасный" вариант по умолчанию в случае ошибки
        return {"list": "Chores", "label": "notes"}