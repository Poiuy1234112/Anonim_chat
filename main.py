# main.py
import logging
import asyncio
import os
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton

# Получаем токен и ID группы из переменных окружения
API_TOKEN = os.getenv("API_TOKEN")  # Токен бота
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))  # ID группы (преобразуем в int)

# Проверяем, что переменные окружения заданы
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

@router.message(Command('help'))
async def send_help(message: types.Message):
    photo = FSInputFile("help_image.png")
    await message.answer_photo(
        photo,
        caption=" Команды-помошь:\n"
                "/start - Начать работу с ботом\n"
                "/begin - Начать анонимный чат\n"
                "/end - Завершить анонимный чат\n"
                "/help - Получить справку\n"
                "/git - Ссылка на GitHub-репозиторий бота\n\n"
                "ПРИМЕЧАНИЕ: после окончания диалога советую ЗАКРЫВАТЬ чат а когда надо открывать новый для большей анонимности\n"
                "версия бота 1.4 визуальный интерфейс\n"
                "добавлен гитхаб  при любых проблемах или если вы хотите лично кзнать как рбаотет бот пришите @Andre_Niks",
        reply_markup=get_command_keyboard()
    )

@router.message(Command('git'))
async def send_git(message: types.Message):
    await message.reply("GitHub-репозиторий бота: https://github.com/Poiuy1234112/Anonim_chat", reply_markup=get_command_keyboard())

@router.message(Command('begin'))
async def begin_chat(message: types.Message):
    user_id = message.from_user.id

    if user_id in user_to_topic:
        await message.reply("❌ У тебя уже есть активный чат. Нажми /end чтобы завершить его", reply_markup=get_command_keyboard())
        return

    try:
        topic_id = await create_topic(user_id)
        user_to_topic[user_id] = topic_id
        topic_to_user[topic_id] = user_id

        await message.reply(f"Чат создан! Ты можешь начинать писать сообщения :)  Если я не отвечаю пингани @Andre_Niks", reply_markup=get_command_keyboard())

        await bot.send_message(
            chat_id=GROUP_CHAT_ID,
            message_thread_id=topic_id,
            text=f"Новый анонимный запрос от пользователя #За_работу @Andre_Niks"
        )

    except Exception as e:
        logger.error(f"Ошибка создания топика: {e}")
        await message.reply("⚠️ Не удалось создать чат. Попробуй позже", reply_markup=get_command_keyboard())

@router.message(Command('end'))
async def end_chat(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_to_topic:
        await message.reply("❌ У тебя нет активных чатов", reply_markup=get_command_keyboard())
        return

    try:
        topic_id = user_to_topic[user_id]
        await close_topic(topic_id)
        del user_to_topic[user_id]
        del topic_to_user[topic_id]
        await message.reply("✅ Чат успешно завершен", reply_markup=get_command_keyboard())

    except Exception as e:
        logger.error(f"Ошибка закрытия топика: {e}")
        await message.reply("⚠️ Не удалось завершить чат. Обратись к администратору @Andre_Niks", reply_markup=get_command_keyboard())

@router.callback_query(F.data == "start")
async def callback_start(callback: types.CallbackQuery):
    await send_welcome(callback.message)

@router.callback_query(F.data == "help")
async def callback_help(callback: types.CallbackQuery):
    await send_help(callback.message)

@router.callback_query(F.data == "begin")
async def callback_begin(callback: types.CallbackQuery):
    await begin_chat(callback.message)

@router.callback_query(F.data == "end")
async def callback_end(callback: types.CallbackQuery):
    await end_chat(callback.message)

@router.callback_query(F.data == "git")
async def callback_git(callback: types.CallbackQuery):
    await send_git(callback.message)

@router.message(F.chat.id > 0)  # Личные сообщения
async def handle_user_message(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_to_topic:
        await message.reply("❌ Сначала начни чат командой /begin", reply_markup=get_command_keyboard())
        return

    topic_id = user_to_topic[user_id]

    if message.text:
        await bot.send_message(
            chat_id=GROUP_CHAT_ID,
            message_thread_id=topic_id,
            text=f"Сообщение от пользователя:\n{message.text}"
        )
    elif message.sticker:
        await bot.send_sticker(
            chat_id=GROUP_CHAT_ID,
            message_thread_id=topic_id,
            sticker=message.sticker.file_id
        )
    elif message.photo:
        await bot.send_photo(
            chat_id=GROUP_CHAT_ID,
            message_thread_id=topic_id,
            photo=message.photo[-1].file_id,
            caption="Фото от пользователя"
        )
    elif message.animation:
        await bot.send_animation(
            chat_id=GROUP_CHAT_ID,
            message_thread_id=topic_id,
            animation=message.animation.file_id,
            caption="GIF от пользователя"
        )
    elif message.document:
        await bot.send_document(
            chat_id=GROUP_CHAT_ID,
            message_thread_id=topic_id,
            document=message.document.file_id,
            caption="Документ от пользователя"
        )
    elif message.voice:
        await bot.send_voice(
            chat_id=GROUP_CHAT_ID,
            message_thread_id=topic_id,
            voice=message.voice.file_id,
            caption="Голосовое сообщение от пользователя"
        )
    elif message.video:
        await bot.send_video(
            chat_id=GROUP_CHAT_ID,
            message_thread_id=topic_id,
            video=message.video.file_id,
            caption="Видео от пользователя"
        )

@router.message(F.chat.id == GROUP_CHAT_ID)  # Сообщения из группы
async def handle_group_message(message: types.Message):
    logger.info(f"Получено сообщение из группы: {message}")

    if not message.message_thread_id:
        logger.warning("Сообщение не из топика, игнорируем.")
        return

    topic_id = message.message_thread_id

    if topic_id not in topic_to_user:
        logger.warning(f"Топик {topic_id} не найден в topic_to_user.")
        return

    user_id = topic_to_user[topic_id]

    if message.text:
        await bot.send_message(
            chat_id=user_id,
            text=f"Андрей:\n{message.text}"
        )
    elif message.sticker:
        await bot.send_sticker(
            chat_id=user_id,
            sticker=message.sticker.file_id
        )
    elif message.photo:
        await bot.send_photo(
            chat_id=user_id,
            photo=message.photo[-1].file_id,
            caption="Андрей:"
        )
    elif message.animation:
        await bot.send_animation(
            chat_id=user_id,
            animation=message.animation.file_id,
            caption="Андрей:"
        )
    elif message.document:
        await bot.send_document(
            chat_id=user_id,
            document=message.document.file_id,
            caption="Андрей:"
        )
    elif message.voice:
        await bot.send_voice(
            chat_id=user_id,
            voice=message.voice.file_id,
            caption="Андрей:"
        )
    elif message.video:
        await bot.send_video(
            chat_id=user_id,
            video=message.video.file_id,
            caption="Андрей:"
        )

# Запуск бота
async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
