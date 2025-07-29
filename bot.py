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
PORT = int(os.getenv("PORT", 10000))  # Render requires this

# Initialize OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Initialize conversation history
conversations = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when user sends /start"""
    user = update.message.from_user
    await update.message.reply_text(
        f"Hello {user.first_name}! I'm Mick Your AI. Ask me anything!"
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
        # Generate response using ChatGPT-3.5 (corrected API call)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=conversations[user_id],
            max_tokens=500,
            temperature=0.7
        )
        
        # Get AI reply
        ai_reply = response.choices[0].message.content
        
        # Add to history
        conversations[user_id].append({"role": "assistant", "content": ai_reply})
        
        # Split long messages (>4000 characters)
        if len(ai_reply) > 4000:
            for i in range(0, len(ai_reply), 4000):
                await update.message.reply_text(ai_reply[i:i+4000])
        else:
            await update.message.reply_text(ai_reply)
    
    except Exception as e:
        error_msg = f"🚫 Error: {str(e)}"
        await update.message.reply_text(error_msg[:4000])  # Truncate long errors

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset conversation history with /reset"""
    user_id = update.message.from_user.id
    conversations[user_id] = [{"role": "system", "content": "You're a helpful assistant"}]
    await update.message.reply_text("♻️ Conversation history cleared!")

def main() -> None:
    # Create Telegram application
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Determine running environment
    if "RENDER" in os.environ:
        # Webhook mode for Render
        public_url = os.getenv("RENDER_EXTERNAL_URL")
        print(f"🤖 Starting webhook mode on {public_url}")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"{public_url}/webhook",
            drop_pending_updates=True
        )
    else:
        # Polling mode for local development
        print("🤖 Starting polling mode...")
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )

if __name__ == "__main__":
    main()
