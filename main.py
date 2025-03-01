import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),  # Log to a file
        logging.StreamHandler()  # Log to the console
    ]
)
logger = logging.getLogger(__name__)

# Load manager chat IDs from environment variable
def load_manager_chat_ids():
    manager_chat_ids = os.getenv("MANAGER_CHAT_IDS", "")
    return [int(id.strip()) for id in manager_chat_ids.split(",")] if manager_chat_ids else []

MANAGER_CHAT_IDS = load_manager_chat_ids()

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

# Styled "Back" button
BACK_BUTTON = "⬅️ Назад"

# Dictionary to store the relationship between user and manager messages
user_manager_messages = {}

# Command /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.message.from_user.username} started the bot.")
    keyboard = [[category] for category in QUESTIONS.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Вас приветствует бот для доноров🩸\n"
        "Вы можете написать вопрос менеджеру в строке ниже или выбрать категорию часто задаваемых вопросов:",
        reply_markup=reply_markup
    )

# Handle user messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_chat_id = update.message.chat_id
    user_message_id = update.message.message_id
    user_username = update.message.from_user.username

    # Log the received message
    logger.info(f"[handle_message] Пользователь @{user_username} (ID: {user_chat_id}) отправил сообщение: {user_message}")

    # Skip processing if the message is from a manager and is a reply
    if update.message.from_user.id in MANAGER_CHAT_IDS and update.message.reply_to_message:
        logger.info(f"[handle_message] Сообщение от менеджера @{user_username} (ID: {user_chat_id}) пропущено, так как это ответ.")
        return

    if user_message == BACK_BUTTON:
        # Handle "Back" button
        keyboard = [[category] for category in QUESTIONS.keys()]
        reply_markup = ReplyKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите категорию:", reply_markup=reply_markup)
        logger.info(f"[handle_message] Пользователь @{user_username} (ID: {user_chat_id}) нажал кнопку 'Назад'.")
    elif user_message in QUESTIONS:
        # Show questions for the selected category
        keyboard = [[question] for question in QUESTIONS[user_message]] + [[BACK_BUTTON]]
        reply_markup = ReplyKeyboardMarkup(keyboard)
        await update.message.reply_text(f"Вопросы в категории '{user_message}':", reply_markup=reply_markup)
        logger.info(f"[handle_message] Пользователь @{user_username} (ID: {user_chat_id}) выбрал категорию: {user_message}.")
    elif user_message in REPLIES:
        # Send the answer if the question is in the list
        await update.message.reply_text(REPLIES[user_message])
        logger.info(f"[handle_message] Пользователь @{user_username} (ID: {user_chat_id}) задал вопрос: {user_message}. Ответ: {REPLIES[user_message]}")
    else:
        # Forward the message to the first manager (or implement round-robin logic)
        if MANAGER_CHAT_IDS:
            manager_chat_id = MANAGER_CHAT_IDS[0]  # Forward to the first manager

            try:
                # Forward the message
                forwarded_message = await context.bot.forward_message(
                    chat_id=manager_chat_id,
                    from_chat_id=user_chat_id,
                    message_id=user_message_id
                )

                # Log the forwarded message
                logger.info(f"[handle_message] Сообщение пользователя @{user_username} (ID: {user_chat_id}) переслано менеджеру (ID: {manager_chat_id}). ID пересланного сообщения: {forwarded_message.message_id}.")

                # Store the relationship between the forwarded message and the user
                user_manager_messages[forwarded_message.message_id] = {
                    "user_chat_id": user_chat_id,
                    "user_username": user_username,
                    "user_message_id": user_message_id
                }

                # Log the stored relationship
                logger.info(f"[handle_message] Связь сохранена: ID пересланного сообщения {forwarded_message.message_id} -> Пользователь @{user_username} (ID: {user_chat_id}).")

                await update.message.reply_text("Ваш вопрос передан менеджеру. Ожидайте ответа.")
            except Exception as e:
                logger.error(f"[handle_message] Ошибка при пересылке сообщения менеджеру (ID: {manager_chat_id}): {e}")
                await update.message.reply_text("Произошла ошибка при пересылке вопроса менеджеру. Пожалуйста, попробуйте позже.")
        else:
            logger.warning("[handle_message] Нет менеджеров для пересылки сообщения.")
            await update.message.reply_text("В настоящее время нет доступных менеджеров. Пожалуйста, попробуйте позже.")
# Temporary handler to log group ID
async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Group ID: {update.message.chat.id}")

# Handle manager replies
async def handle_manager_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Log the incoming message
    logger.info(f"[handle_manager_reply] Входящее сообщение от пользователя @{update.message.from_user.username} (ID: {update.message.from_user.id}).")

    # Check if the message is from a manager
    if update.message.from_user.id in MANAGER_CHAT_IDS:
        manager_username = update.message.from_user.username
        manager_id = update.message.from_user.id

        # Log manager information
        logger.info(f"[handle_manager_reply] Менеджер @{manager_username} (ID: {manager_id}) отправил сообщение.")

        # Check if the message is a reply
        if update.message.reply_to_message:
            replied_message_id = update.message.reply_to_message.message_id

            # Log the replied message
            logger.info(f"[handle_manager_reply] Менеджер @{manager_username} (ID: {manager_id}) ответил на сообщение с ID {replied_message_id}.")

            # Check if the replied message is linked to a user
            if replied_message_id in user_manager_messages:
                user_data = user_manager_messages[replied_message_id]
                user_chat_id = user_data["user_chat_id"]
                user_username = user_data["user_username"]

                # Log the forwarding of the reply to the user
                logger.info(f"[handle_manager_reply] Ответ менеджера @{manager_username} (ID: {manager_id}) пересылается пользователю @{user_username} (ID: {user_chat_id}).")

                # Send the manager's reply to the user
                await context.bot.send_message(
                    chat_id=user_chat_id,
                    text=f"Ответ от менеджера: {update.message.text}"
                )

                # Log the deletion of the relationship
                logger.info(f"[handle_manager_reply] Запись для сообщения с ID {replied_message_id} удалена из user_manager_messages.")

                # Remove the relationship from the dictionary
                del user_manager_messages[replied_message_id]
            else:
                # Log if the relationship is not found
                logger.warning(f"[handle_manager_reply] Связь для сообщения с ID {replied_message_id} не найдена в user_manager_messages.")
        else:
            # Log if the message is not a reply
            logger.info(f"[handle_manager_reply] Менеджер @{manager_username} (ID: {manager_id}) отправил сообщение, но оно не является ответом на другое сообщение.")
    else:
        # Log if the message is not from a manager
        logger.info(f"[handle_manager_reply] Сообщение от пользователя @{update.message.from_user.username} (ID: {update.message.from_user.id}) не обрабатывается как ответ менеджера.")

# Main function
def main():
    # Load the bot token from environment variable
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("No BOT_TOKEN environment variable found!")

    # Create the Application
    app = Application.builder().token(TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(user_id=MANAGER_CHAT_IDS) & filters.REPLY, handle_manager_reply))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    # Register the temporary handler
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_group_message))
    # Start the bot with webhook
    app.run_webhook(
        listen="0.0.0.0",  # Listen on all interfaces
        port=5000,  # Port to listen on
        url_path=TOKEN,  # Webhook path (use bot token for security)
        webhook_url=f"https://donorknows.onrender.com/{TOKEN}"  # Full webhook URL
    )

if __name__ == "__main__":
    main()