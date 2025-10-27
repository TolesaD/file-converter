import os
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import Config

# Import handlers - keep these at top level
from handlers.start import start_command, help_command, handle_callback, show_history
from handlers.conversion import handle_file
from handlers.history import show_history as show_user_history, handle_history_callback
from handlers.admin import admin_command, show_admin_stats, handle_admin_callback, handle_broadcast_message, confirm_broadcast

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_init(application):
    """Post initialization setup - Set bot commands"""
    try:
        await application.bot.set_my_commands([
            ("start", "Start the bot and show main menu"),
            ("help", "Show help information and usage guide"),
            ("history", "View your conversion history"),
        ])
        print("✅ Bot commands have been set successfully!")
        
        # Import queue manager here to avoid circular imports
        from queue_manager import queue_manager
        # Start queue manager in background
        asyncio.create_task(queue_manager.process_queue())
        print("🚀 Queue manager started")
        
    except Exception as e:
        print(f"❌ Error in post_init: {e}")

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(Config.BOT_TOKEN).post_init(post_init).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("history", show_user_history))
    
    # Admin command handlers (only work for admins)
    application.add_handler(CommandHandler("stats", show_admin_stats))
    application.add_handler(CommandHandler("admin", admin_command))
    
    # Callback query handlers
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # File handlers
    application.add_handler(MessageHandler(
        filters.Document.ALL | filters.PHOTO | filters.AUDIO | filters.VIDEO,
        handle_file
    ))
    
    # Broadcast message handler
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_broadcast_message
    ))
    
    # Start the bot
    if os.getenv('RAILWAY_ENVIRONMENT'):
        # Running on Railway
        port = int(os.getenv('PORT', 8443))
        url = os.getenv('RAILWAY_STATIC_URL')
        
        if url:
            application.run_webhook(
                listen="0.0.0.0",
                port=port,
                url_path=Config.BOT_TOKEN,
                webhook_url=f"{url}/{Config.BOT_TOKEN}"
            )
        else:
            application.run_polling()
    else:
        # Running locally
        print("🤖 Bot is running...")
        print("📊 Use /start to begin")
        print("🔧 Bot commands have been set")
        print("🚀 Multi-user queue system active")
        print("👑 Admin features enabled")
        print("🧠 Smart conversion system ready")
        application.run_polling()

if __name__ == '__main__':
    import asyncio
    main()