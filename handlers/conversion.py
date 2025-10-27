import os
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from database import db
from queue_manager import queue_manager
from utils.keyboard_utils import get_main_menu_keyboard, get_format_suggestions_keyboard
from handlers.start import detect_file_type
import logging

logger = logging.getLogger(__name__)

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle uploaded files with smart detection - MAIN ENTRY POINT"""
    user = update.effective_user
    user_id = user.id
    
    logger.info(f"File upload from user {user_id}")
    
    # Get file information
    if update.message.document:
        file = update.message.document
        file_name = file.file_name or "file"
        file_extension = file_name.split('.')[-1].lower() if '.' in file_name else 'bin'
    elif update.message.photo:
        file = update.message.photo[-1]
        file_extension = 'jpg'
        file_name = f"photo_{datetime.now().strftime('%H%M%S')}.jpg"
    elif update.message.audio:
        file = update.message.audio
        file_extension = 'mp3'
        file_name = file.file_name or f"audio_{datetime.now().strftime('%H%M%S')}.mp3"
    elif update.message.video:
        file = update.message.video
        file_extension = 'mp4'
        file_name = file.file_name or f"video_{datetime.now().strftime('%H%M%S')}.mp4"
    else:
        await update.message.reply_text("❌ Unsupported file type!")
        return
    
    # Check file size
    if file.file_size > 50 * 1024 * 1024:
        await update.message.reply_text("❌ File too large! Maximum size is 50MB.")
        return
    
    # Download file first
    progress_msg = await update.message.reply_text("📥 Downloading your file...")
    
    try:
        file_obj = await file.get_file()
        input_path = f"temp/uploads/{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
        await file_obj.download_to_drive(input_path)
        
        logger.info(f"File downloaded to: {input_path}")
        
        # Store the downloaded file path in context for later use
        context.user_data['last_downloaded_file'] = {
            'path': input_path,
            'extension': file_extension,
            'name': file_name,
            'size': file.file_size
        }
        
        # Check if this is a follow-up upload after conversion type selection
        if context.user_data.get('expecting_followup_upload'):
            # This is a follow-up upload after conversion type selection
            context.user_data.pop('expecting_followup_upload', None)
            await process_file_directly(update, context, input_path, file_extension, user_id)
        else:
            # This is a random upload - show conversion options
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
    """Detect file type and show conversion suggestions"""
    
    try:
        # Detect file type
        file_type, category_name = detect_file_type(file_extension)
        
        if file_type == 'unknown':
            await update.message.reply_text(
                f"❌ Unknown file type: .{file_extension}\n\n"
                f"Please use the menu to select conversion type manually.",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            # Clean up the file since we can't use it
            if os.path.exists(input_path):
                os.remove(input_path)
            return
        
        # Store file info for later use in conversions
        context.user_data['detected_file_info'] = {
            'path': input_path,
            'extension': file_extension,
            'type': file_type,
            'name': file_name
        }
        
        logger.info(f"File detected as: {file_type} ({file_extension})")
        
        # Show smart suggestions
        suggestion_text = f"""
🧠 *Smart File Detection*

📁 File: `{file_name}`
🔍 Type: .{file_extension.upper()} ({category_name})
📊 Size: {context.user_data['last_downloaded_file']['size'] // 1024} KB

💡 *I can convert this to:*
        """
        
        await update.message.reply_text(
            suggestion_text,
            reply_markup=get_format_suggestions_keyboard(file_extension, file_type),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in file detection: {e}")
        await update.message.reply_text(f"❌ Error analyzing file: {str(e)}")
        
        # Cleanup on error
        if os.path.exists(input_path):
            try:
                os.remove(input_path)
            except:
                pass

async def process_file_directly(update, context, input_path, file_extension, user_id):
    """Process file when conversion type is already selected"""
    
    try:
        # Get conversion details from context
        conversion_type = context.user_data.get('conversion_type', '')
        output_format = context.user_data.get('output_format', '')
        
        logger.info(f"Processing file: {conversion_type} -> {output_format}")
        
        if not conversion_type or not output_format:
            await update.message.reply_text(
                "❌ Conversion type not set. Please select a conversion type first.",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            # Clean up the file since we can't process it
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
            'file_size': os.path.getsize(input_path)
        }
        
        # Add to queue
        job_id, queue_position = await queue_manager.add_to_queue(job_data)
        
        # Send queue confirmation
        queue_message = f"✅ *File queued for processing!*\n\n"
        queue_message += f"🆔 Job ID: `{job_id}`\n"
        queue_message += f"📊 Queue position: `{queue_position}`\n"
        queue_message += f"🎯 Conversion: `{file_extension.upper()} → {output_format.upper()}`\n\n"
        queue_message += "⏳ You'll receive progress updates shortly..."
        
        if hasattr(update, 'message'):
            await update.message.reply_text(queue_message, parse_mode='Markdown')
        else:
            # Handle case when update is a callback query
            await update.edit_message_text(queue_message, parse_mode='Markdown')
        
        # Clear conversion data but keep user context
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
        
        if hasattr(update, 'message'):
            await update.message.reply_text(error_message)
        else:
            await update.edit_message_text(error_message)
        
        # Cleanup on error
        if os.path.exists(input_path):
            try:
                os.remove(input_path)
            except:
                pass

async def handle_smart_conversion_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle file upload after smart conversion type selection"""
    user = update.effective_user
    user_id = user.id
    
    logger.info(f"Smart conversion file upload from user {user_id}")
    
    # Get file information
    if update.message.document:
        file = update.message.document
        file_extension = file.file_name.split('.')[-1].lower() if file.file_name else 'bin'
    elif update.message.photo:
        file = update.message.photo[-1]
        file_extension = 'jpg'
    elif update.message.audio:
        file = update.message.audio
        file_extension = 'mp3'
    elif update.message.video:
        file = update.message.video
        file_extension = 'mp4'
    else:
        await update.message.reply_text("❌ Unsupported file type!")
        return
    
    # Check file size
    if file.file_size > 50 * 1024 * 1024:
        await update.message.reply_text("❌ File too large! Maximum size is 50MB.")
        return
    
    # Download and process the file
    progress_msg = await update.message.reply_text("📥 Downloading your file...")
    
    try:
        file_obj = await file.get_file()
        input_path = f"temp/uploads/{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
        await file_obj.download_to_drive(input_path)
        
        logger.info(f"Smart conversion file downloaded to: {input_path}")
        
        await process_file_directly(update, context, input_path, file_extension, user_id)
            
    except Exception as e:
        logger.error(f"Error in smart conversion for user {user_id}: {e}")
        await progress_msg.edit_text(f"❌ Error: {str(e)}")
        
        # Cleanup on error
        if 'input_path' in locals() and os.path.exists(input_path):
            try:
                os.remove(input_path)
            except:
                pass