from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
# Токен вашего бота
TOKEN = ''

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

# ID менеджера или группы (можно получить через @userinfobot)
MANAGER_CHAT_ID = 1120634377
    #411379581

# Стилизованная кнопка "Назад"
BACK_BUTTON = "⬅️ Назад"

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

# Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    logger.info(f"User {update.message.from_user.username} sent: {user_message}")

    if user_message == BACK_BUTTON:
        # Если нажата кнопка "Назад", возвращаемся к выбору категории
        keyboard = [[category] for category in QUESTIONS.keys()]
        reply_markup = ReplyKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите категорию:", reply_markup=reply_markup)
    elif user_message in QUESTIONS:
        # Если выбрана категория, показываем вопросы из этой категории
        keyboard = [[question] for question in QUESTIONS[user_message]] + [[BACK_BUTTON]]
        reply_markup = ReplyKeyboardMarkup(keyboard)
        await update.message.reply_text(f"Вопросы в категории '{user_message}':", reply_markup=reply_markup)
    elif user_message in REPLIES:
        # Если вопрос есть в списке, отправляем ответ
        await update.message.reply_text(REPLIES[user_message])
    else:
        # Если вопроса нет, пересылаем менеджеру
        await context.bot.send_message(
            chat_id=MANAGER_CHAT_ID,
            text=f"Новый вопрос от пользователя @{update.message.from_user.username}:\n{user_message}"
        )
        await update.message.reply_text("Ваш вопрос передан менеджеру. Ожидайте ответа.")


# Основная функция
def main():
    app = Application.builder().token(TOKEN).build()

    # Регистрируем команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    app.run_polling()

if __name__ == "__main__":
    main()