# services/llm_service.py
import openai
import json
import logging
from my_config import OPENAI_API_KEY, TRELLO_LISTS, TRELLO_LABELS

client = openai.OpenAI(api_key=OPENAI_API_KEY)

def get_note_category(text: str) -> dict:
    """
    Использует LLM для определения колонки и меток для заметки.
    """
    prompt = """
    You are an expert Trello categorization assistant. Your task is to perform two distinct actions based on a user's note:
    1.  **Classify into a List**: Determine the single most appropriate list for the card. The lists represent the overall nature of the task.
    2.  **Assign Labels**: Identify all relevant topics within the note to assign as labels. A single note can have multiple labels.

    **Step 1: Choose ONE List Category**
    - 'Poker, AI, Crypto': Use for specific, actionable tasks, learning goals, or work related to these three high-tech/analytical fields.
    - 'Идеи, мысли, цитаты': Use for abstract ideas, creative sparks, quotes, philosophical thoughts, and content ideas. This is for less concrete, more conceptual notes.
    - 'Бытовуха': Use for everyday chores, errands, appointments, shopping, reminders, and anything that is a simple life-log or doesn't fit the other two categories. This is the default.

    **Step 2: Choose ONE OR MORE Label Keywords**
    These are topics that can apply to a note in ANY list.
    - 'health': Medicine, doctors, fitness, health, pills, sports.
    - 'networking': Meetings, calls, social events, making contacts.
    - 'crypto': Cryptocurrency, blockchain, bitcoin, ethereum, tokens.
    - 'poker': Poker, GTO, strategy, game analysis.
    - 'art': Art, creativity, design, content creation, video/photo shooting ideas.
    - 'ai': Artificial Intelligence, LLM, models, machine learning, CS50.
    - 'notes': The default label for general notes, chores, or anything that doesn't fit a specific topic. Use this if no other label is appropriate.

    **Example Scenarios:**
    - Note: "купить таблетки от головы" -> List: 'Бытовуха', Labels: ['health']
    - Note: "Идея для статьи про использование AI в медицине" -> List: 'Идеи, мысли, цитаты', Labels: ['ai', 'health']
    - Note: "Проанализировать вчерашнюю покерную сессию" -> List: 'Poker, AI, Crypto', Labels: ['poker']
    - Note: "Не забыть забрать пальто из химчистки" -> List: 'Бытовуха', Labels: ['notes']

    You MUST respond with a JSON object with two keys:
    - "list_category": A string, one of ['Poker, AI, Crypto', 'Идеи, мысли, цитаты', 'Бытовуха'].
    - "label_keywords": A list of one or more strings from ['health', 'networking', 'crypto', 'poker', 'art', 'ai', 'notes'].
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"User note: \"{text}\""}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # --- List Logic ---
        list_category = result.get("list_category")
        if list_category not in TRELLO_LISTS:
            logging.warning(f"LLM вернула неверную категорию списка: {list_category}. Использую 'Бытовуха'.")
            list_category = "Бытовуха"

        # --- Label Logic ---
        label_keywords = result.get("label_keywords", [])
        if not isinstance(label_keywords, list) or not label_keywords:
            label_keywords = ["notes"]

        # Map keywords to Trello Label IDs
        trello_label_ids = []
        for key in label_keywords:
            if key in TRELLO_LABELS and "ADD_" not in TRELLO_LABELS[key]:
                trello_label_ids.append(TRELLO_LABELS[key])
            else:
                logging.warning(f"Ключевое слово метки '{key}' не найдено или его ID не задан в config.")
        
        # Ensure there's at least one label
        if not trello_label_ids:
            trello_label_ids.append(TRELLO_LABELS["notes"])

        return {
            "category": list_category, # For Google Sheets column
            "trello_list_id": TRELLO_LISTS[list_category],
            "trello_label_ids": list(set(trello_label_ids)) # Ensure unique IDs
        }

    except Exception as e:
        logging.error(f"Ошибка при работе с LLM: {e}")
        return {
            "category": "Бытовуха",
            "trello_list_id": TRELLO_LISTS["Бытовуха"],
            "trello_label_ids": [TRELLO_LABELS["notes"]]
        }