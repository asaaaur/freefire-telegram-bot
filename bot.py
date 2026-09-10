import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import time
from collections import defaultdict

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Spam detection settings
MAX_MESSAGES = 5  # Max messages per user
TIME_WINDOW = 10  # Time window in seconds
MAX_CAPS_RATIO = 0.7  # Maximum ratio of capital letters

# Store user message history
user_messages = defaultdict(list)
warned_users = defaultdict(int)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! 👋\n\n"
        "Welcome to Free Fire Bot! 🔥\n\n"
        "This is a spam-free community bot.\n\n"
        "Available commands:\n"
        "/help - Show help\n"
        "/stats - View player stats\n"
        "/report - Report spam",
        reply_markup=None
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
🤖 **Free Fire Bot Commands:**

/start - Start the bot
/help - Show this help message
/stats <username> - Get player stats
/report <message> - Report spam
/warn - Check your warning count

⚠️ **Anti-Spam Rules:**
• No spamming messages rapidly
• No excessive CAPS
• No repeated characters
• Violations result in warnings

3 warnings = Mute ❌
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def check_spam(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if message is spam. Returns True if spam detected."""
    user_id = update.effective_user.id
    message_text = update.message.text
    current_time = time.time()
    
    # Check rapid messaging
    user_messages[user_id] = [
        timestamp for timestamp in user_messages[user_id]
        if current_time - timestamp < TIME_WINDOW
    ]
    
    if len(user_messages[user_id]) >= MAX_MESSAGES:
        return True
    
    user_messages[user_id].append(current_time)
    
    # Check for excessive caps
    if len(message_text) > 5:
        caps_ratio = sum(1 for c in message_text if c.isupper()) / len(message_text)
        if caps_ratio > MAX_CAPS_RATIO:
            return True
    
    # Check for repeated characters
    for i in range(len(message_text) - 3):
        if message_text[i] == message_text[i+1] == message_text[i+2]:
            if message_text[i] not in ' ':
                return True
    
    return False

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages and check for spam."""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if await check_spam(update, context):
        warned_users[user_id] += 1
        warnings = warned_users[user_id]
        
        if warnings >= 3:
            await update.message.reply_text(
                f"❌ {user_name}, you have been muted for spam violations.\n"
                f"Total warnings: {warnings}"
            )
        else:
            await update.message.reply_text(
                f"⚠️ Warning #{warnings}: Please don't spam!\n"
                f"(3 warnings = Mute)"
            )
    else:
        # Normal message - you can add features here
        await update.message.reply_text("✅ Message received!")

async def report_spam(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle spam reports."""
    if not context.args:
        await update.message.reply_text("Usage: /report <description of spam>")
        return
    
    report_text = " ".join(context.args)
    admin_message = f"📋 Spam Report from {update.effective_user.first_name}:\n{report_text}"
    
    await update.message.reply_text("✅ Report submitted! Thank you for keeping the community safe.")
    logger.info(admin_message)

async def warn_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check user's warning count."""
    user_id = update.effective_user.id
    warnings = warned_users.get(user_id, 0)
    await update.message.reply_text(f"⚠️ Your current warnings: {warnings}/3")

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token("YOUR_TELEGRAM_BOT_TOKEN").build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("report", report_spam))
    application.add_handler(CommandHandler("warn", warn_status))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()
