from telegram import Update
from telegram.ext import ContextTypes
from database import db
from utils.keyboard_utils import get_main_menu_keyboard

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's conversion history"""
    user = update.effective_user
    user_id = user.id
    
    history = db.get_user_history(user_id)
    
    if not history:
        await update.message.reply_text(
            "📊 You haven't done any conversions yet!\nUse the menu to start converting files.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    history_text = "📊 *Your Conversion History*\n\n"
    
    for i, item in enumerate(history[:10]):  # Show last 10
        status_emoji = "✅" if item['success'] else "❌"
        history_text += f"{i+1}. {status_emoji} {item['input_type'].upper()} → {item['output_type'].upper()}\n"
        history_text += f"   📏 Size: {item['input_size']} → {item['output_size']} bytes\n"
        history_text += f"   🕐 {item['timestamp'][:16]}\n\n"
    
    if len(history) > 10:
        history_text += f"... and {len(history) - 10} more conversions"
    
    await update.message.reply_text(history_text, parse_mode='Markdown')

async def handle_history_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle history callback from inline keyboard"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    history = db.get_user_history(user_id)
    
    if not history:
        await query.edit_message_text(
            "📊 You haven't done any conversions yet!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Create a more detailed history view for callback
    history_text = "📊 *Your Conversion History*\n\n"
    total_conversions = len(history)
    successful = sum(1 for h in history if h['success'])
    
    history_text += f"📈 Statistics:\n"
    history_text += f"• Total conversions: {total_conversions}\n"
    history_text += f"• Successful: {successful}\n"
    history_text += f"• Success rate: {(successful/total_conversions)*100:.1f}%\n\n"
    
    history_text += "🕐 Recent conversions:\n"
    for i, item in enumerate(history[:5]):
        status_emoji = "✅" if item['success'] else "❌"
        history_text += f"{i+1}. {status_emoji} {item['input_type']} → {item['output_type']}\n"
    
    from utils.keyboard_utils import get_main_menu_keyboard
    await query.edit_message_text(
        history_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )