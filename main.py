# main.py
import logging
import asyncio
import os
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton

# Получаем токен, ID группы и стоп-код из переменных окружения
API_TOKEN = os.getenv("API_TOKEN")  # Токен бота
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))  # ID группы (преобразуем в int)
STOP_CODE = os.getenv("STOP_CODE")  # Секретный код для остановки

# Проверяем обязательные переменные окружения
if not API_TOKEN or not GROUP_CHAT_ID:
    raise ValueError("Не заданы переменные окружения API_TOKEN или GROUP_CHAT_ID")

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

# Хранилище данных: user_id → topic_id
user_to_topic = {}
topic_to_user = {}

# Функции для работы с топиками
async def create_topic(user_id: int) -> int:
    """Создает топик в группе-форуме и возвращает его ID"""
    topic = await bot.create_forum_topic(
        chat_id=GROUP_CHAT_ID,
        name=f"Анонимный чат"
    )
    return topic.message_thread_id

async def close_topic(topic_id: int):
    """Закрывает топик"""
    await bot.close_forum_topic(
        chat_id=GROUP_CHAT_ID,
        message_thread_id=topic_id
    )

# Клавиатура с кнопками
def get_command_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать", callback_data="start"),
         InlineKeyboardButton(text="Помощь", callback_data="help")],
        [InlineKeyboardButton(text="Начать чат", callback_data="begin"),
         InlineKeyboardButton(text="Завершить чат", callback_data="end")],
        [InlineKeyboardButton(text="GitHub", callback_data="git")]
    ])
    return keyboard

# Обработчики команд
@router.message(Command('stop'))
async def stop_command(message: types.Message):
    """Обработчик команды /stop с секретным кодом"""
    args = message.text.split()
    if len(args) < 2:
        await message.reply("❌ Необходимо предоставить секретный код. Использование: /stop <код>")
        return
    
    user_code = args[1]
    if user_code != STOP_CODE:
        await message.reply("❌ Неверный секретный код.")
        return
    
    await message.reply("🛑 Активирован стоп-кран. Остановка бота...")
    logger.info("Стоп-кран активирован, останавливаю бота...")
    
    # Останавливаем поллинг и закрываем соединения
    await dp.stop_polling()
    await bot.session.close()

@router.message(Command('start'))
async def send_welcome(message: types.Message):
    photo = FSInputFile("start_image.png")
    await message.answer_photo(
        photo,
        caption="Привет Я бот для анонимного общения с Андрем\n"
        "и данный юот предназначен для обсуждения личных проблем со мной макчимально анонимно :)\n (настольок что у мення открытый код) \n"
        "чтобы понять как пользаватся ботом пишите /help \n\n"
        "и если что меня вообше не волнует на каие темы вы будете со мной обшатся всегда готов потдержать ^^",
        reply_markup=get_command_keyboard()
    )

# ... (остальные обработчики остаются без изменений)

# Запуск бота
async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    # Запуск воркера с обработкой асинхронных задач
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
