# services/gspread_service.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
from datetime import datetime

# --- Configuration ---
SCOPE = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
CREDS_FILE = 'credentials.json'

# --- Columns we expect in the Google Sheet ---
EXPECTED_COLUMNS = ["Дата", "Poker, AI, Crypto", "Идеи, мысли, цитаты", "Бытовуха"]

def _get_credentials():
    try:
        return ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
    except FileNotFoundError:
        logging.error(f"Файл {CREDS_FILE} не найден.")
        return None

def get_service_account_email():
    creds_info = _get_credentials()
    return creds_info.service_account_email if creds_info else None

def add_note_to_sheet(note: str, category: str, sheet_url: str) -> bool:
    """
    Добавляет заметку в Google Таблицу в соответствующую категорию с датой.
    """
    creds = _get_credentials()
    if not creds:
        return False
        
    try:
        client = gspread.authorize(creds)
        sheet = client.open_by_url(sheet_url).sheet1

        # Check for header and create if not present
        header = sheet.row_values(1)
        if header != EXPECTED_COLUMNS:
            sheet.clear()
            sheet.append_row(EXPECTED_COLUMNS)
            logging.info("Создан заголовок в Google Sheets.")

        # Prepare the row with the correct structure
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_row = ["" for _ in EXPECTED_COLUMNS]
        new_row[0] = now # Date in the first column

        try:
            # Find the index of the category column
            category_index = EXPECTED_COLUMNS.index(category)
            new_row[category_index] = note
        except ValueError:
            # If category is somehow invalid, put it in 'Бытовуха'
            misc_index = EXPECTED_COLUMNS.index("Бытовуха")
            new_row[misc_index] = note
            logging.warning(f"Категория '{category}' не найдена, запись добавлена в 'Бытовуха'.")

        sheet.append_row(new_row)
        logging.info(f"Заметка '{note}' добавлена в Google Sheets в категорию '{category}'.")
        return True

    except gspread.exceptions.SpreadsheetNotFound:
        logging.error(f"Таблица не найдена по URL: {sheet_url}")
        return False
    except Exception as e:
        logging.error(f"Произошла ошибка при работе с Google Sheets: {e}")
        return False