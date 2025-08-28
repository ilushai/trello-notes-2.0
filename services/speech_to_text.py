# services/speech_to_text.py
import openai
from my_config import OPENAI_API_KEY

# Убедитесь, что ваш OpenAI клиент инициализирован с API ключом
# Используем асинхронный клиент, так как бот работает асинхронно
client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)

async def speech_to_text(audio_file_path: str) -> str: # <--- Добавляем async
    """
    Преобразует аудиофайл в текст с помощью OpenAI Whisper.
    """
    try:
        with open(audio_file_path, "rb") as audio_file:
            # Вызов API тоже должен быть асинхронным
            transcript = await client.audio.transcriptions.create( # <--- Добавляем await
                model="whisper-1", 
                file=audio_file
            )
        return transcript.text
    except Exception as e:
        print(f"Ошибка при распознавании речи: {e}")
        return "Не удалось распознать речь."