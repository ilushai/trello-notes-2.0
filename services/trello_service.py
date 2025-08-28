# services/trello_service.py
import requests
import logging
from my_config import TRELLO_API_KEY, TRELLO_TOKEN

def create_trello_card(name: str, list_id: str, label_id: str):
    """
    Создает карточку в Trello в указанном списке с указанной меткой.
    """
    if not all([TRELLO_API_KEY, TRELLO_TOKEN, list_id, label_id]):
        logging.warning("Ключи или ID для Trello не настроены. Пропускаю создание карточки.")
        return False, None, None

    url = "https://api.trello.com/1/cards"
    query = {
        'key': TRELLO_API_KEY,
        'token': TRELLO_TOKEN,
        'idList': list_id,
        'name': name,
        'idLabels': label_id
    }

    try:
        response = requests.post(url, params=query)
        response.raise_for_status()
        logging.info(f"Карточка Trello '{name}' успешно создана.")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при создании карточки Trello: {e}")
        return False