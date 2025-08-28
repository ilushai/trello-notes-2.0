# services/gspread_service.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
from threading import Lock
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(os.path.dirname(BASE_DIR), 'credentials.json')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
gs_lock = Lock()

SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

def get_sheet_by_url(spreadsheet_url: str):
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url(spreadsheet_url)
        return spreadsheet.sheet1
    except Exception as e:
        logging.error(f"Ошибка при подключении к Google Sheets по ссылке: {e}")
        return None

def add_note_to_sheet(text: str, spreadsheet_url: str):
    with gs_lock:
        sheet = get_sheet_by_url(spreadsheet_url)
        if sheet:
            try:
                list_of_values = sheet.col_values(1)
                next_row = len(list_of_values) + 1
                sheet.update_cell(next_row, 1, text)
                logging.info(f"Заметка успешно сохранена в Google Sheets.")
                return True
            except Exception as e:
                logging.error(f"Не удалось записать данные в Google Sheets: {e}")
                return False
        return False

def get_service_account_email():
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        return creds.service_account_email
    except Exception as e:
        logging.error(f"Не удалось прочитать email из файла credentials.json. Ошибка: {e}")
        return None