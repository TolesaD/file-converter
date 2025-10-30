import os
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import db
from queue_manager import queue_manager
from utils.keyboard_utils import get_main_menu_keyboard, get_format_suggestions_keyboard
from handlers.start import detect_file_type
from config import Config
import logging

logger = logging.getLogger(__name__)

async def is_user_banned(user_id):
    """Check if user is banned"""
    user = db.get_user_by_id(user_id)
    return user and user['is_banned']

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle uploaded files with smart detection - FIXED FLOW"""
    user = update.effective_user
    user_id = user.id
    
    # Check if user is banned
    if await is_user_banned(user_id):
        await update.message.reply_text(
            "🚫 *Account Banned*\n\n"
            "Your account has been banned from using this bot. "
            "If you believe this is a mistake, please contact the administrator.",
            parse_mode='Markdown'
        )
        return
    
    logger.info(f"File upload from user {user_id}")
    
    # Get file information
    file = None
    file_name = ""
    file_extension = ""
    file_type = "document"  # default
    
    if update.message.document:
        file = update.message.document
        file_name = file.file_name or "file"
        file_extension = file_name.split('.')[-1].lower() if '.' in file_name else 'bin'
        file_type = "document"
    elif update.message.photo:
        file = update.message.photo[-1]
        file_extension = 'jpg'
        file_name = f"photo_{datetime.now().strftime('%H%M%S')}.jpg"
        file_type = "photo"
    elif update.message.audio:
        file = update.message.audio
        file_extension = file.file_name.split('.')[-1].lower() if file.file_name and '.' in file.file_name else 'mp3'
        file_name = file.file_name or f"audio_{datetime.now().strftime('%H%M%S')}.{file_extension}"
        file_type = "audio"
    elif update.message.video:
        file = update.message.video
        file_extension = file.file_name.split('.')[-1].lower() if file.file_name and '.' in file.file_name else 'mp4'
        file_name = file.file_name or f"video_{datetime.now().strftime('%H%M%S')}.{file_extension}"
        file_type = "video"
    else:
        await update.message.reply_text("❌ Unsupported file type!")
        return
    
    # Check file size
    if file.file_size > Config.MAX_FILE_SIZE:
        await update.message.reply_text(
            f"❌ File too large! Maximum size is 2GB.\n"
            f"Your file: {file.file_size // (1024*1024*1024)}GB",
            parse_mode='Markdown'
        )
        return
    
    # Download file with progress
    file_size_mb = file.file_size // (1024 * 1024) if file.file_size else 0
    progress_msg = await update.message.reply_text(f"📥 Downloading your file ({file_size_mb}MB)...")
    
    try:
        file_obj = await file.get_file()
        input_path = f"temp/uploads/{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
        
        # Ensure upload directory exists
        os.makedirs(os.path.dirname(input_path), exist_ok=True)
        
        await file_obj.download_to_drive(input_path)
        
        logger.info(f"File downloaded to: {input_path} (Size: {file.file_size} bytes, Type: {file_type})")
        
        # Store file info
        context.user_data['last_downloaded_file'] = {
            'path': input_path,
            'extension': file_extension,
            'name': file_name,
            'size': file.file_size,
            'type': file_type
        }
        
        # Check if this is a follow-up upload (user already selected conversion)
        if context.user_data.get('expecting_followup_upload'):
            context.user_data.pop('expecting_followup_upload', None)
            await process_file_directly(update, context, input_path, file_extension, user_id, file_name)
        else:
            # Show automatic detection and suggestions
            await detect_and_suggest_conversions(update, context, file_extension, file_name, user_id, input_path)
            
    except Exception as e:
        logger.error(f"Error handling file for user {user_id}: {e}")
        await progress_msg.edit_text(f"❌ Error: {str(e)}")
        
        # Cleanup on error
        if 'input_path' in locals() and os.path.exists(input_path):
            try:
                os.remove(input_path)
            except:
                pass

async def detect_and_suggest_conversions(update, context, file_extension, file_name, user_id, input_path):
    """Detect file type and show smart conversion suggestions - FIXED"""
    
    try:
        # Detect file type using the smart detection function
        file_type, category_name = detect_file_type(file_extension)
        
        if file_type == 'unknown':
            await update.message.reply_text(
                f"❌ Unsupported file type: .{file_extension}\n\n"
                f"Please use the menu to browse supported formats.",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            # Clean up the file
            if os.path.exists(input_path):
                os.remove(input_path)
            return
        
        # Store file info for later use
        context.user_data['detected_file_info'] = {
            'path': input_path,
            'extension': file_extension,
            'type': file_type,
            'name': file_name,
            'category': category_name
        }
        
        logger.info(f"File detected as: {file_type} ({file_extension}) - {category_name}")
        
        # Show smart suggestions with better formatting
        file_size_mb = context.user_data['last_downloaded_file']['size'] // (1024 * 1024) if context.user_data['last_downloaded_file']['size'] else 0
        
        suggestion_text = f"""
🧠 *Smart File Detection - Complete!*

📁 File: `{file_name}`
🔍 Type: `.{file_extension.upper()}` ({category_name})
📊 Size: `{file_size_mb} MB`

💡 *I can convert this to these formats:*
"""
        
        # Get smart suggestions keyboard
        keyboard = get_format_suggestions_keyboard(file_extension, file_type)
        
        await update.message.reply_text(
            suggestion_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in file detection: {e}")
        await update.message.reply_text(
            f"❌ Error analyzing file: {str(e)}\n\nPlease try uploading again or use the menu.",
            reply_markup=get_main_menu_keyboard(user_id)
        )
        
        # Cleanup on error
        if os.path.exists(input_path):
            try:
                os.remove(input_path)
            except:
                pass

async def process_file_directly(update, context, input_path, file_extension, user_id, file_name):
    """Process file when conversion type is already selected - FIXED"""
    
    try:
        # Check if user is banned
        if await is_user_banned(user_id):
            await update.message.reply_text(
                "🚫 *Account Banned*\n\n"
                "Your account has been banned from using this bot. "
                "If you believe this is a mistake, please contact the administrator.",
                parse_mode='Markdown'
            )
            # Clean up the file
            if os.path.exists(input_path):
                os.remove(input_path)
            return
        
        # Get conversion details from context
        conversion_type = context.user_data.get('conversion_type', '')
        output_format = context.user_data.get('output_format', '')
        
        logger.info(f"Processing direct conversion: {file_extension} -> {output_format}")
        
        if not conversion_type or not output_format:
            error_msg = "❌ Conversion type not set. Please select a conversion type first."
            
            await update.message.reply_text(
                error_msg,
                reply_markup=get_main_menu_keyboard(user_id)
            )
            
            # Clean up the file
            if os.path.exists(input_path):
                os.remove(input_path)
            return
        
        # Verify the uploaded file matches expected format
        expected_input = conversion_type.split('_to_')[0] if '_to_' in conversion_type else ''
        if expected_input and file_extension.lower() != expected_input.lower():
            await update.message.reply_text(
                f"❌ File type mismatch!\n\n"
                f"Expected: `.{expected_input.upper()}`\n"
                f"Uploaded: `.{file_extension.upper()}`\n\n"
                f"Please upload the correct file type.",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard(user_id)
            )
            # Clean up the file
            if os.path.exists(input_path):
                os.remove(input_path)
            return
        
        # Prepare job data
        job_data = {
            'user_id': user_id,
            'input_path': input_path,
            'output_format': output_format,
            'conversion_type': conversion_type,
            'input_type': file_extension,
            'file_size': os.path.getsize(input_path),
            'original_file_name': file_name,
            'update': update,
            'context': context
        }
        
        # Add to queue
        job_id, queue_position = await queue_manager.add_to_queue(job_data)
        
        # Send queue confirmation
        queue_message = f"""
✅ *File Queued for Processing!*

🆔 Job ID: `{job_id}`
📋 Queue Position: `{queue_position}`
🎯 Conversion: `{file_extension.upper()} → {output_format.upper()}`

⏳ You'll receive progress updates shortly...
"""
        
        await update.message.reply_text(queue_message, parse_mode='Markdown')
        
        # Clear conversion data but keep menu state
        context.user_data.pop('conversion_type', None)
        context.user_data.pop('output_format', None)
        context.user_data.pop('file_type', None)
        context.user_data.pop('last_downloaded_file', None)
        context.user_data.pop('detected_file_info', None)
        context.user_data.pop('expecting_followup_upload', None)
        
        logger.info(f"✅ File queued for user {user_id}, job {job_id}")
            
    except Exception as e:
        logger.error(f"Error processing file for user {user_id}: {e}")
        error_message = f"❌ Error processing file: {str(e)}"
        
        await update.message.reply_text(error_message)
        
        # Cleanup on error
        if os.path.exists(input_path):
            try:
                os.remove(input_path)
            except:
                pass

async def send_conversion_result(update, context, result_path, original_file_name, output_format, success=True, error_message=None):
    """Send conversion result with persistent menu - FIXED"""
    try:
        user_id = update.effective_user.id
        
        if success and os.path.exists(result_path):
            # Send the converted file
            file_size = os.path.getsize(result_path)
            file_size_mb = file_size / (1024 * 1024)
            
            # Create continue menu
            continue_keyboard = [
                [InlineKeyboardButton("🔄 Convert Another File", callback_data="convert_file")],
                [InlineKeyboardButton("📤 Upload Another File", callback_data="upload_now")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            ]
            
            caption = f"""
✅ *Conversion Successful!*

📁 Original: `{original_file_name}`
🔄 Converted to: `{output_format.upper()}`
📊 Size: `{file_size_mb:.1f} MB`

What would you like to do next?
"""
            
            # Send as document for better compatibility
            await update.message.reply_document(
                document=open(result_path, 'rb'),
                filename=f"{original_file_name.rsplit('.', 1)[0]}.{output_format}",
                caption=caption,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(continue_keyboard)
            )
            
            # Clean up files
            try:
                if os.path.exists(result_path):
                    os.remove(result_path)
            except:
                pass
                
        else:
            error_msg = error_message or "Conversion failed"
            
            continue_keyboard = [
                [InlineKeyboardButton("🔄 Try Again", callback_data="convert_file")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            ]
            
            await update.message.reply_text(
                f"❌ *Conversion Failed*\n\nError: {error_msg}\n\nPlease try again or contact support.",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(continue_keyboard)
            )
            
    except Exception as e:
        logger.error(f"Error sending conversion result: {e}")
        
        continue_keyboard = [
            [InlineKeyboardButton("🔄 Convert Another File", callback_data="convert_file")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        ]
        
        await update.message.reply_text(
            "❌ Error sending result, but conversion may have completed. Check your files.",
            reply_markup=InlineKeyboardMarkup(continue_keyboard)
        )