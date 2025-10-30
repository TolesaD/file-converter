import os
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import db
from queue_manager import queue_manager
from utils.keyboard_utils import get_main_menu_keyboard, get_format_suggestions_keyboard
from handlers.start import detect_file_type, get_continue_keyboard
from config import Config
import logging

logger = logging.getLogger(__name__)

async def is_user_banned(user_id):
    """Check if user is banned"""
    user = db.get_user_by_id(user_id)
    return user and user['is_banned']

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle uploaded files with smart detection"""
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
    
    # Get file information with proper format detection
    file = None
    file_name = "file"
    file_extension = "bin"
    
    if update.message.document:
        file = update.message.document
        file_name = file.file_name or "document"
        if '.' in file_name:
            file_extension = file_name.split('.')[-1].lower()
        else:
            # Try to detect from MIME type
            if file.mime_type:
                if 'image' in file.mime_type:
                    file_extension = 'jpg'
                elif 'audio' in file.mime_type:
                    file_extension = 'mp3'
                elif 'video' in file.mime_type:
                    file_extension = 'mp4'
                elif 'pdf' in file.mime_type:
                    file_extension = 'pdf'
                elif 'word' in file.mime_type:
                    file_extension = 'docx'
                elif 'excel' in file.mime_type:
                    file_extension = 'xlsx'
                elif 'text' in file.mime_type:
                    file_extension = 'txt'
                    
    elif update.message.photo:
        file = update.message.photo[-1]
        file_extension = 'jpg'
        file_name = f"photo_{datetime.now().strftime('%H%M%S')}.jpg"
    elif update.message.audio:
        file = update.message.audio
        file_extension = 'mp3'
        file_name = file.file_name or f"audio_{datetime.now().strftime('%H%M%S')}.mp3"
        # Try to get actual format from file name
        if file.file_name and '.' in file.file_name:
            file_extension = file.file_name.split('.')[-1].lower()
    elif update.message.video:
        file = update.message.video
        file_extension = 'mp4'
        file_name = file.file_name or f"video_{datetime.now().strftime('%H%M%S')}.mp4"
        if file.file_name and '.' in file.file_name:
            file_extension = file.file_name.split('.')[-1].lower()
    else:
        await update.message.reply_text("❌ Unsupported file type!")
        return
    
    # Fix GIF detection (sometimes detected as video)
    if file_extension == 'mp4' and file_name.lower().endswith('.gif'):
        file_extension = 'gif'
        file_name = file_name.rsplit('.', 1)[0] + '.gif'
    
    # Check file size against REAL Telegram limits
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
        os.makedirs(os.path.dirname(input_path), exist_ok=True)
        await file_obj.download_to_drive(input_path)
        
        logger.info(f"File downloaded to: {input_path} (Size: {file.file_size} bytes, Format: {file_extension})")
        
        # Store file info
        context.user_data['last_downloaded_file'] = {
            'path': input_path,
            'extension': file_extension,
            'name': file_name,
            'size': file.file_size
        }
        
        # Check if this is a follow-up upload
        if context.user_data.get('expecting_followup_upload'):
            context.user_data.pop('expecting_followup_upload', None)
            await process_file_directly(update, context, input_path, file_extension, user_id, progress_msg)
        else:
            # Show conversion options with smart detection
            await detect_and_suggest_conversions(update, context, file_extension, file_name, user_id, input_path, progress_msg)
            
    except Exception as e:
        logger.error(f"Error handling file for user {user_id}: {e}")
        await progress_msg.edit_text(f"❌ Error: {str(e)}")
        
        # Cleanup on error
        if 'input_path' in locals() and os.path.exists(input_path):
            try:
                os.remove(input_path)
            except:
                pass

async def detect_and_suggest_conversions(update, context, file_extension, file_name, user_id, input_path, progress_msg):
    """Detect file type and show smart conversion suggestions"""
    
    try:
        # Detect file type using the smart detection function
        file_type, category_name = detect_file_type(file_extension)
        
        if file_type == 'unknown':
            await progress_msg.edit_text(
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
            'name': file_name
        }
        
        logger.info(f"File detected as: {file_type} ({file_extension}) - {category_name}")
        
        # Show smart suggestions
        file_size_mb = context.user_data['last_downloaded_file']['size'] // (1024 * 1024)
        suggestion_text = f"""
🧠 *Smart File Detection*

📁 File: `{file_name}`
🔍 Type: .{file_extension.upper()} ({category_name})
📊 Size: {file_size_mb} MB

💡 *I can convert this to:*
"""
        
        await progress_msg.edit_text(
            suggestion_text,
            reply_markup=get_format_suggestions_keyboard(file_extension, file_type),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in file detection: {e}")
        await progress_msg.edit_text(f"❌ Error analyzing file: {str(e)}")
        
        # Cleanup on error
        if os.path.exists(input_path):
            try:
                os.remove(input_path)
            except:
                pass

async def process_file_directly(update, context, input_path, file_extension, user_id, progress_msg):
    """Process file when conversion type is already selected"""
    
    try:
        # Check if user is banned (in case they were banned during upload)
        if await is_user_banned(user_id):
            await progress_msg.edit_text(
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
        
        logger.info(f"Processing file: {file_extension} -> {output_format}")
        
        if not conversion_type or not output_format:
            error_msg = "❌ Conversion type not set. Please select a conversion type first."
            
            await progress_msg.edit_text(
                error_msg,
                reply_markup=get_main_menu_keyboard(user_id)
            )
            
            # Clean up the file
            if os.path.exists(input_path):
                os.remove(input_path)
            return
        
        # Verify the input format matches expected type
        expected_format = context.user_data.get('file_type', '')
        if expected_format and file_extension.lower() != expected_format.lower():
            await progress_msg.edit_text(
                f"❌ Format mismatch!\n\n"
                f"Expected: .{expected_format.upper()}\n"
                f"Received: .{file_extension.upper()}\n\n"
                f"Please send a {expected_format.upper()} file.",
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
            'progress_message': progress_msg
        }
        
        # Add to queue
        job_id, queue_position = await queue_manager.add_to_queue(job_data)
        
        # Send queue confirmation
        queue_message = f"✅ *File queued for processing!*\n\n"
        queue_message += f"🆔 Job ID: `{job_id}`\n"
        queue_message += f"📋 Queue position: `{queue_position}`\n"
        queue_message += f"🎯 Conversion: `{file_extension.upper()} → {output_format.upper()}`\n\n"
        queue_message += "⏳ You'll receive progress updates shortly..."
        
        await progress_msg.edit_text(queue_message, parse_mode='Markdown')
        
        # Clear conversion data but keep menu available
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
        
        await progress_msg.edit_text(
            error_message,
            reply_markup=get_continue_keyboard()
        )
        
        # Cleanup on error
        if os.path.exists(input_path):
            try:
                os.remove(input_path)
            except:
                pass

# Enhanced function to send conversion result with menu
async def send_conversion_result(user_id, original_message, result_path, output_format, conversion_successful=True):
    """Send conversion result with continue options"""
    if conversion_successful:
        # Determine file type for sending
        file_type = 'document'  # default
        
        if output_format in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
            file_type = 'photo'
        elif output_format in ['mp3', 'wav', 'aac']:
            file_type = 'audio'
        elif output_format in ['mp4', 'avi', 'mov', 'mkv']:
            file_type = 'video'
        
        try:
            # Send the converted file
            with open(result_path, 'rb') as file:
                if file_type == 'photo':
                    await original_message.reply_photo(
                        photo=file,
                        caption=f"✅ Successfully converted to {output_format.upper()}!",
                        reply_markup=get_continue_keyboard()
                    )
                elif file_type == 'audio':
                    await original_message.reply_audio(
                        audio=file,
                        caption=f"✅ Successfully converted to {output_format.upper()}!",
                        reply_markup=get_continue_keyboard()
                    )
                elif file_type == 'video':
                    await original_message.reply_video(
                        video=file,
                        caption=f"✅ Successfully converted to {output_format.upper()}!",
                        reply_markup=get_continue_keyboard()
                    )
                else:
                    await original_message.reply_document(
                        document=file,
                        caption=f"✅ Successfully converted to {output_format.upper()}!",
                        reply_markup=get_continue_keyboard()
                    )
        except Exception as e:
            logger.error(f"Error sending file: {e}")
            await original_message.reply_text(
                f"✅ Conversion successful but error sending file: {str(e)}",
                reply_markup=get_continue_keyboard()
            )
    else:
        await original_message.reply_text(
            f"❌ Conversion failed: {result_path}",
            reply_markup=get_continue_keyboard()
        )