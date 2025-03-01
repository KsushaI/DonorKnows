from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
import os

# Read the bot token from an environment variable
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("No BOT_TOKEN environment variable found!")

# List of questions by category
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

# Answers to questions
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

# Manager or group ID (can be obtained via @userinfobot)
MANAGER_CHAT_ID = 1120634377

# Styled "Back" button
BACK_BUTTON = "⬅️ Назад"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),  # Log to file
        logging.StreamHandler()  # Log to console
    ]
)
logger = logging.getLogger(__name__)

# Command /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.message.from_user.username} started the bot.")
    keyboard = [[category] for category in QUESTIONS.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard)
    await update.message.reply_text("Вас приветствует бот для доноров🩸\nВы можете написать вопрос менеджеру в строке ниже или выбрать категорию часто задаваемых вопросов:", reply_markup=reply_markup)

# Handle text messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    logger.info(f"User {update.message.from_user.username} sent: {user_message}")

    if user_message == BACK_BUTTON:
        # If "Back" button is pressed, return to category selection
        keyboard = [[category] for category in QUESTIONS.keys()]
        reply_markup = ReplyKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите категорию:", reply_markup=reply_markup)
    elif user_message in QUESTIONS:
        # If a category is selected, show questions from that category
        keyboard = [[question] for question in QUESTIONS[user_message]] + [[BACK_BUTTON]]
        reply_markup = ReplyKeyboardMarkup(keyboard)
        await update.message.reply_text(f"Вопросы в категории '{user_message}':", reply_markup=reply_markup)
    elif user_message in REPLIES:
        # If the question is in the list, send the answer
        await update.message.reply_text(REPLIES[user_message])
    else:
        # If the question is not in the list, forward it to the manager
        await context.bot.send_message(
            chat_id=MANAGER_CHAT_ID,
            text=f"Новый вопрос от пользователя @{update.message.from_user.username}:\n{user_message}"
        )
        await update.message.reply_text("Ваш вопрос передан менеджеру. Ожидайте ответа.")

# Main function
def main():
    app = Application.builder().token(TOKEN).build()

    # Register commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    # Set webhook
    app.run_webhook(
        listen="0.0.0.0",  # Listen on all interfaces
        port=5000,  # Port to listen on
        url_path=TOKEN,  # Webhook path (use bot token for security)
        webhook_url=f"https://donorknows.onrender.com/{TOKEN}"  # Full webhook URL
    )

if __name__ == "__main__":
    main()