import os
import openai
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Initialize conversation history
conversations = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when user sends /start"""
    user = update.message.from_user
    await update.message.reply_text(
        f"Hello {user.first_name}! I'm your ChatGPT-3.5 bot. Ask me anything!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process user messages with ChatGPT-3.5"""
    user_id = update.message.from_user.id
    user_message = update.message.text
    
    # Initialize conversation history if new user
    if user_id not in conversations:
        conversations[user_id] = [
            {"role": "system", "content": "You're a helpful assistant"}
        ]
    
    # Add user message to history
    conversations[user_id].append({"role": "user", "content": user_message})
    
    try:
        # Generate response using ChatGPT-3.5
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversations[user_id],
            max_tokens=500,
            temperature=0.7
        )
        
        # Get AI reply and add to history
        ai_reply = response.choices[0].message['content']
        conversations[user_id].append({"role": "assistant", "content": ai_reply})
        
        # Send response to user
        await update.message.reply_text(ai_reply)
    
    except Exception as e:
        error_msg = f"🚫 Error: {str(e)}"
        await update.message.reply_text(error_msg)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset conversation history with /reset"""
    user_id = update.message.from_user.id
    conversations[user_id] = [{"role": "system", "content": "You're a helpful assistant"}]
    await update.message.reply_text("♻️ Conversation history cleared!")

if __name__ == "__main__":
    # Create Telegram application
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start bot
    print("🤖 ChatGPT-3.5 Telegram Bot is running...")
    app.run_polling()
