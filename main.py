from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
import os

# Чтение токена бота из переменной окружения
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("No BOT_TOKEN environment variable found!")

# Список вопросов по категориям
QUESTIONS = {
    "Общие вопросы": [
        "Что случится с плазмой?",
        "Нужно ли мне приходить повторно?",
        "Когда я получу статус почётного донора?"
    ],
    "Второе": ["1?", "2?", "3?", "4?", "5?", "6?"],
    "Другое": [
        "Куда я попал?"
    ]
}

# Ответы на вопросы
REPLIES = {
    "Что случится с плазмой?": "Её проверят на безопасность",
    "Нужно ли мне приходить повторно?": "Да, приходи, мы тебя ждём ;)",
    "Когда я получу статус почётного донора?": "Очень нескоро",
    "1?": "1.",
    "2?": "2.",
    "3?": "3.",
    "4?": "4.",
    "5?": "5.",
    "6?": "6.",
    "Куда я попал?": "Сюда",
}

# ID менеджера или группы
MANAGER_CHAT_ID = 1120634377

# Стилизованная кнопка "Назад"
BACK_BUTTON = "⬅️ Назад"

# Словарь для хранения связи между сообщениями пользователя и менеджера
user_manager_messages = {}

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),  # Логирование в файл
        logging.StreamHandler()  # Логирование в консоль
    ]
)
logger = logging.getLogger(__name__)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.message.from_user.username} started the bot.")
    keyboard = [[category] for category in QUESTIONS.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard)
    await update.message.reply_text("Вас приветствует бот для доноров🩸\nВы можете написать вопрос менеджеру в строке ниже или выбрать категорию часто задаваемых вопросов:", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_chat_id = update.message.chat_id
    user_message_id = update.message.message_id
    user_username = update.message.from_user.username  # Получаем username пользователя

    # Логируем полученное сообщение от пользователя
    logger.info(f"[handle_message] Пользователь @{user_username} (ID: {user_chat_id}) отправил сообщение: {user_message}")

    # Проверяем, является ли сообщение от менеджера и является ли оно ответом
    if update.message.from_user.id == MANAGER_CHAT_ID and update.message.reply_to_message:
        logger.info(f"[handle_message] Сообщение от менеджера @{user_username} (ID: {user_chat_id}) пропущено, так как это ответ.")
        return  # Пропускаем обработку ответов менеджера

    if user_message == BACK_BUTTON:
        # Если нажата кнопка "Назад", возвращаемся к выбору категории
        keyboard = [[category] for category in QUESTIONS.keys()]
        reply_markup = ReplyKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите категорию:", reply_markup=reply_markup)
        logger.info(f"[handle_message] Пользователь @{user_username} (ID: {user_chat_id}) нажал кнопку 'Назад'.")
    elif user_message in QUESTIONS:
        # Если выбрана категория, показываем вопросы из этой категории
        keyboard = [[question] for question in QUESTIONS[user_message]] + [[BACK_BUTTON]]
        reply_markup = ReplyKeyboardMarkup(keyboard)
        await update.message.reply_text(f"Вопросы в категории '{user_message}':", reply_markup=reply_markup)
        logger.info(f"[handle_message] Пользователь @{user_username} (ID: {user_chat_id}) выбрал категорию: {user_message}.")
    elif user_message in REPLIES:
        # Если вопрос есть в списке, отправляем ответ
        await update.message.reply_text(REPLIES[user_message])
        logger.info(f"[handle_message] Пользователь @{user_username} (ID: {user_chat_id}) задал вопрос: {user_message}. Ответ: {REPLIES[user_message]}")
    else:
        # Если вопроса нет, пересылаем сообщение менеджеру
        forwarded_message = await context.bot.forward_message(
            chat_id=MANAGER_CHAT_ID,
            from_chat_id=user_chat_id,
            message_id=user_message_id
        )

        # Логируем пересылку сообщения менеджеру
        logger.info(f"[handle_message] Сообщение пользователя @{user_username} (ID: {user_chat_id}) переслано менеджеру. ID пересланного сообщения: {forwarded_message.message_id}.")

        # Сохраняем связь между сообщением менеджера и пользователя
        user_manager_messages[forwarded_message.message_id] = {
            "user_chat_id": user_chat_id,
            "user_username": user_username,
            "user_message_id": user_message_id
        }

        # Логируем сохранение связи в словаре
        logger.info(f"[handle_message] Связь сохранена: ID пересланного сообщения {forwarded_message.message_id} -> Пользователь @{user_username} (ID: {user_chat_id}).")

        await update.message.reply_text("Ваш вопрос передан менеджеру. Ожидайте ответа.")

async def handle_manager_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Логируем входящее сообщение
    logger.info(f"[handle_manager_reply] Входящее сообщение от пользователя @{update.message.from_user.username} (ID: {update.message.from_user.id}).")

    # Check if the message is from the manager
    if update.message.from_user.id == MANAGER_CHAT_ID:
        # Получаем username и ID менеджера
        manager_username = update.message.from_user.username
        manager_id = update.message.from_user.id

        # Логируем информацию о менеджере
        logger.info(f"[handle_manager_reply] Менеджер @{manager_username} (ID: {manager_id}) отправил сообщение.")

        # Проверяем, является ли сообщение ответом на другое сообщение
        if update.message.reply_to_message:
            replied_message_id = update.message.reply_to_message.message_id

            # Логируем факт получения ответа от менеджера
            logger.info(f"[handle_manager_reply] Менеджер @{manager_username} (ID: {manager_id}) ответил на сообщение с ID {replied_message_id}.")

            # Проверяем, есть ли связь между этим сообщением и пользователем
            if replied_message_id in user_manager_messages:
                user_data = user_manager_messages[replied_message_id]
                user_chat_id = user_data["user_chat_id"]
                user_username = user_data["user_username"]  # Получаем username пользователя

                # Логируем отправку ответа пользователю
                logger.info(
                    f"[handle_manager_reply] Ответ менеджера @{manager_username} (ID: {manager_id}) пересылается пользователю @{user_username} (ID: {user_chat_id})."
                )

                # Отправляем ответ менеджера пользователю
                await context.bot.send_message(
                    chat_id=user_chat_id,
                    text=f"Ответ от менеджера: {update.message.text}"
                )

                # Логируем удаление записи из словаря
                logger.info(f"[handle_manager_reply] Запись для сообщения с ID {replied_message_id} удалена из user_manager_messages.")

                # Удаляем запись из словаря (опционально)
                del user_manager_messages[replied_message_id]
            else:
                # Логируем, если связь не найдена
                logger.warning(f"[handle_manager_reply] Связь для сообщения с ID {replied_message_id} не найдена в user_manager_messages.")
        else:
            # Логируем, если сообщение не является ответом
            logger.info(f"[handle_manager_reply] Менеджер @{manager_username} (ID: {manager_id}) отправил сообщение, но оно не является ответом на другое сообщение.")
    else:
        # Логируем, если сообщение не от менеджера
        logger.info(f"[handle_manager_reply] Сообщение от пользователя @{update.message.from_user.username} (ID: {update.message.from_user.id}) не обрабатывается как ответ менеджера.")
# Основная функция
def main():
    app = Application.builder().token(TOKEN).build()

    # Регистрируем команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Регистрируем обработчик для ответов менеджера
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_manager_reply))

    # Запуск бота
    app.run_webhook(
        listen="0.0.0.0",  # Listen on all interfaces
        port=5000,  # Port to listen on
        url_path=TOKEN,  # Webhook path (use bot token for security)
        webhook_url=f"https://donorknows.onrender.com/{TOKEN}"  # Full webhook URL
    )

if __name__ == "__main__":
    main()