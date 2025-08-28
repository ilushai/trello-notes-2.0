# bot.py
import logging
import os
import json
from aiogram import Bot, Dispatcher, executor, types
from functools import wraps

# --- Импорты (без изменений) ---
from my_config import TELEGRAM_BOT_TOKEN, TRELLO_LISTS, TRELLO_LABELS
from user_config import AUTHORIZED_USERS, ADMIN_USERNAME, ADMIN_ID
from services.gspread_service import add_note_to_sheet, get_service_account_email
from services.speech_to_text import speech_to_text
from services.trello_service import create_trello_card
from services.llm_service import get_trello_details

# --- (Код до handle_voice не меняется) ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)
USER_SHEETS_FILE = 'user_sheets.json'
def load_user_sheets():
    if not os.path.exists(USER_SHEETS_FILE): return {}
    try:
        with open(USER_SHEETS_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except json.JSONDecodeError: return {}
def save_user_sheets(data):
    with open(USER_SHEETS_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4, ensure_ascii=False)
user_sheets = load_user_sheets()
def authorized_only(handler):
    @wraps(handler)
    async def wrapper(message: types.Message, *args, **kwargs):
        if message.from_user.id not in AUTHORIZED_USERS:
            await message.reply(f"❌ **Доступ запрещен.**\n\nДля получения доступа обратитесь к: {ADMIN_USERNAME}"); return
        return await handler(message, *args, **kwargs)
    return wrapper
@dp.message_handler(commands=['start', 'help'])
@authorized_only
async def send_welcome(message: types.Message):
    user_id = str(message.from_user.id); sheet_url = user_sheets.get(user_id)
    service_email = get_service_account_email()
    if not service_email: await message.answer("Ошибка: не удается прочитать `credentials.json`."); return
    instructions = (f"👋 **Привет! Это твой бот для заметок.**\n\n...")
    if sheet_url: instructions += f"\n✅ **Текущая таблица:** [Ссылка]({sheet_url})"
    else: instructions += f"\n❌ **Статус:** Таблица не настроена."
    await message.answer(instructions, parse_mode='Markdown', disable_web_page_preview=True)
@dp.message_handler(commands=['set_sheet'])
@authorized_only
async def set_sheet(message: types.Message):
    user_id = str(message.from_user.id); sheet_url = message.get_args()
    if not sheet_url or not sheet_url.startswith('https://docs.google.com/spreadsheets/d/'):
        await message.reply("Пожалуйста, отправьте валидную ссылку на Google Таблицу."); return
    user_sheets[user_id] = sheet_url; save_user_sheets(user_sheets)
    await message.reply(f"✅ Отлично! Заметки будут сохраняться в эту таблицу.")
@dp.message_handler(commands=['my_sheet'])
@authorized_only
async def my_sheet(message: types.Message):
    user_id = str(message.from_user.id); sheet_url = user_sheets.get(user_id)
    if sheet_url: await message.reply(f"Текущая таблица: [Ссылка]({sheet_url})", parse_mode='Markdown')
    else: await message.reply("Таблица еще не настроена.")
async def process_note(message: types.Message, text: str):
    user_id = message.from_user.id; sheet_url = user_sheets.get(str(user_id))
    if not sheet_url: await message.reply("⚠️ **Сначала нужно настроить таблицу!**"); return
    if add_note_to_sheet(text, sheet_url):
        reply_text = "✅ Записал в Google Sheets."
        if user_id == ADMIN_ID:
            details = await get_trello_details(text)
            list_name, label_name = details["list"], details["label"]
            list_id, label_id = TRELLO_LISTS.get(list_name), TRELLO_LABELS.get(label_name)
            if create_trello_card(text, list_id, label_id):
                reply_text = f"✅ Записал в Google Sheets и Trello (в '{list_name}' с меткой '{label_name}')!"
        await message.reply(reply_text)
    else: await message.reply("❌ **Ошибка при записи в Google Sheets!**")
@dp.message_handler(content_types=types.ContentType.TEXT)
@authorized_only
async def handle_text(message: types.Message):
    await process_note(message, message.text)

# --- ОБНОВЛЕННЫЙ ОБРАБОТЧИК ГОЛОСА ---
@dp.message_handler(content_types=types.ContentType.VOICE)
@authorized_only
async def handle_voice(message: types.Message):
    os.makedirs('temp', exist_ok=True); voice_file_path = os.path.join('temp', f"{message.voice.file_id}.ogg")
    try:
        await message.voice.download(destination_file=voice_file_path)
        await message.reply("⏳ Распознаю...")
        # Теперь здесь тоже нужен await
        recognized_text = await speech_to_text(voice_file_path)
        if recognized_text and recognized_text.strip() and "Не удалось распознать речь" not in recognized_text:
            await process_note(message, recognized_text)
        else: await message.reply("Не смог распознать речь в голосовом сообщении.")
    except Exception as e:
        logging.error(f"Ошибка обработки голосового: {e}")
        await message.reply("❌ Не удалось обработать голосовое сообщение.")
    finally:
        if os.path.exists(voice_file_path): os.remove(voice_file_path)

if __name__ == '__main__':
    logging.info("Бот запускается...")
    executor.start_polling(dp, skip_updates=True)