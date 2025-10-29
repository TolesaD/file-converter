import asyncio
import os
from datetime import datetime
from database import db
from config import Config
import logging

logger = logging.getLogger(__name__)

class QueueManager:
    def __init__(self):
        self.processing = False
        self.current_tasks = []
    
    async def add_to_queue(self, job_data):
        """Add a job to the processing queue"""
        try:
            # Check if user is banned before adding to queue
            user = db.get_user_by_id(job_data['user_id'])
            if user and user['is_banned']:
                raise Exception("User account is banned")
            
            # Calculate queue position
            queue_position = db.get_queued_jobs_count() + 1
            
            # Add job to database
            job_id = db.add_conversion_job(
                job_data['user_id'],
                job_data['input_path'],
                job_data['output_format'],
                job_data['input_type'],
                job_data['file_size'],
                queue_position
            )
            
            job_data['job_id'] = job_id
            job_data['queue_position'] = queue_position
            
            # Add to async queue
            await Config.processing_queue.put(job_data)
            
            logger.info(f"📥 Job {job_id} added to queue at position {queue_position}")
            
            return job_id, queue_position
            
        except Exception as e:
            logger.error(f"Error adding job to queue: {e}")
            raise
    
    async def process_queue(self):
        """Process the conversion queue"""
        if self.processing:
            logger.info("Queue processor already running")
            return
        
        self.processing = True
        logger.info("🚀 Professional queue processor started")
        
        try:
            while self.processing:
                # Check if we can process more jobs
                async with Config.job_lock:
                    if Config.active_jobs >= Config.MAX_CONCURRENT_JOBS:
                        await asyncio.sleep(1)
                        continue
                
                # Get next job from queue
                try:
                    job_data = await asyncio.wait_for(Config.processing_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # Check if user is still not banned before processing
                user = db.get_user_by_id(job_data['user_id'])
                if user and user['is_banned']:
                    logger.info(f"Job {job_data['job_id']} cancelled - user {job_data['user_id']} is banned")
                    db.update_conversion_job(job_data['job_id'], status='failed', error_message='User account banned')
                    
                    await self.send_ban_notification(job_data['user_id'], job_data['job_id'])
                    await self.cleanup_files(job_data.get('input_path'))
                    continue
                
                # Update job status to processing
                db.update_conversion_job(job_data['job_id'], status='processing', progress=10)
                
                # Start processing job
                async with Config.job_lock:
                    Config.active_jobs += 1
                
                logger.info(f"🔄 Processing job {job_data['job_id']}, active jobs: {Config.active_jobs}")
                
                # Process the job in background
                task = asyncio.create_task(self.process_job(job_data))
                self.current_tasks.append(task)
                task.add_done_callback(lambda t: self.current_tasks.remove(t))
                
        except Exception as e:
            logger.error(f"Queue processor error: {e}")
        finally:
            self.processing = False
            logger.info("🛑 Queue processor stopped")
    
    async def process_job(self, job_data):
        """Process a single conversion job with professional quality"""
        try:
            logger.info(f"Starting professional conversion for job {job_data['job_id']}")
            
            # Double-check if user is still not banned
            user = db.get_user_by_id(job_data['user_id'])
            if user and user['is_banned']:
                raise Exception("User account banned during processing")
            
            # Send processing started message
            await self.send_status_update(
                job_data['user_id'],
                job_data['job_id'],
                "🔄 Professional conversion started...",
                20,
                f"Converting {job_data['input_type'].upper()} to {job_data['output_format'].upper()}"
            )
            
            # Perform conversion with professional settings
            try:
                output_path = await asyncio.wait_for(
                    self.perform_professional_conversion(job_data),
                    timeout=600  # 10 minute timeout for professional conversion
                )
            except asyncio.TimeoutError:
                raise Exception("Professional conversion timeout - process took too long")
            
            if output_path and os.path.exists(output_path):
                # Verify output quality
                output_size = os.path.getsize(output_path)
                if output_size == 0:
                    raise Exception("Professional conversion produced empty file")
                
                # Update job status
                db.update_conversion_job(
                    job_data['job_id'],
                    status='completed',
                    progress=100,
                    output_file_path=output_path
                )
                
                # Send completion message
                await self.send_status_update(
                    job_data['user_id'],
                    job_data['job_id'],
                    "✅ Professional conversion completed!",
                    100,
                    f"High-quality {job_data['output_format'].upper()} file ready",
                    output_path
                )
                
                # Add to history
                self.add_to_history(job_data, output_path)
                
                logger.info(f"✅ Job {job_data['job_id']} completed with professional quality")
                
            else:
                raise Exception("Professional conversion produced no output")
                
        except Exception as e:
            logger.error(f"Job {job_data['job_id']} professional processing error: {e}")
            db.update_conversion_job(
                job_data['job_id'],
                status='failed',
                error_message=str(e)
            )
            
            await self.send_status_update(
                job_data['user_id'],
                job_data['job_id'],
                f"❌ Professional conversion failed: {str(e)}",
                0
            )
        
        finally:
            # Cleanup and decrement active jobs counter
            async with Config.job_lock:
                Config.active_jobs = max(0, Config.active_jobs - 1)
            
            # Cleanup temporary files
            await self.cleanup_files(job_data.get('input_path'))
    
    async def perform_professional_conversion(self, job_data):
        """Professional conversion using enhanced converter"""
        conversion_type = job_data['conversion_type']
        input_path = job_data['input_path']
        output_format = job_data['output_format']
        input_extension = job_data['input_type'].lower()
        
        # Update progress
        await self.send_status_update(
            job_data['user_id'],
            job_data['job_id'],
            "🎯 Processing with professional settings...",
            50,
            f"Optimizing {input_extension.upper()} to {output_format.upper()}"
        )
        
        try:
            # Use the enhanced universal converter
            from converters.universal_converter import universal_converter
            return await universal_converter.convert_file(input_path, output_format, input_extension)
                
        except Exception as e:
            logger.error(f"Professional conversion error for job {job_data['job_id']}: {e}")
            raise
    
    async def send_status_update(self, user_id, job_id, message, progress, details="", file_path=None):
        """Send professional status update to user with file size handling"""
        try:
            from telegram import Bot
            from utils.file_utils import format_file_size
            
            bot = Bot(Config.BOT_TOKEN)
            
            # Get queue info
            queued_jobs = db.get_user_queued_jobs(user_id)
            current_job = next((job for job in queued_jobs if job['id'] == job_id), None)
            
            status_message = f"🎯 *Professional File Converter*\n\n"
            status_message += f"{message}\n"
            
            if details:
                status_message += f"📝 *Details:* {details}\n"
            
            status_message += f"📊 *Progress:* {progress}%\n"
            
            if current_job and current_job['queue_position'] > 1:
                status_message += f"📋 *Queue Position:* {current_job['queue_position']}\n"
            
            if progress == 100 and file_path:
                # Check file size before sending
                file_size = os.path.getsize(file_path)
                file_ext = file_path.split('.')[-1].upper()
                formatted_size = format_file_size(file_size)
                
                # Telegram file size limits
                MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
                
                if file_size > MAX_FILE_SIZE:
                    # File too large - send informative message
                    caption = f"📁 *File Converted Successfully!*\n\n"
                    caption += f"✅ *Conversion:* Completed\n"
                    caption += f"📊 *Size:* {formatted_size} (Exceeds Telegram's 50MB limit)\n"
                    caption += f"🎯 *Format:* {file_ext}\n"
                    caption += f"💡 *Solution:* The file was converted successfully but is too large for Telegram\n"
                    caption += f"🔧 *Tip:* Try converting to a different format or compress the original file"
                    
                    await bot.send_message(
                        chat_id=user_id,
                        text=caption,
                        parse_mode='Markdown'
                    )
                    
                    logger.info(f"File too large for Telegram: {formatted_size}")
                    return
                
                caption = f"✅ *Professional Conversion Complete!*\n\n"
                caption += f"📁 *Format:* {file_ext}\n"
                caption += f"📊 *Size:* {formatted_size}\n"
                caption += f"🎯 *Quality:* Professional Grade\n"
                caption += f"⚡ *Enjoy your high-quality file!*"
                
                try:
                    if file_ext in ['JPG', 'JPEG', 'PNG', 'WEBP', 'BMP']:
                        # Send images as photos (smaller files)
                        if file_size < 10 * 1024 * 1024:  # 10MB limit for photos
                            await bot.send_photo(
                                chat_id=user_id,
                                photo=open(file_path, 'rb'),
                                caption=caption,
                                parse_mode='Markdown'
                            )
                        else:
                            await bot.send_document(
                                chat_id=user_id,
                                document=open(file_path, 'rb'),
                                caption=caption,
                                parse_mode='Markdown'
                            )
                    elif file_ext == 'GIF':
                        # Always send GIFs as documents to preserve animation
                        await bot.send_document(
                            chat_id=user_id,
                            document=open(file_path, 'rb'),
                            caption=caption,
                            parse_mode='Markdown'
                        )
                    elif file_ext in ['MP3', 'WAV', 'AAC', 'OGG']:
                        # For audio files, use audio method for smaller files
                        if file_size < 20 * 1024 * 1024:  # 20MB limit for audio
                            await bot.send_audio(
                                chat_id=user_id,
                                audio=open(file_path, 'rb'),
                                caption=caption,
                                parse_mode='Markdown'
                            )
                        else:
                            await bot.send_document(
                                chat_id=user_id,
                                document=open(file_path, 'rb'),
                                caption=caption,
                                parse_mode='Markdown'
                            )
                    elif file_ext in ['MP4', 'AVI', 'MOV', 'MKV']:
                        # For video files, use video method for smaller files
                        if file_size < 20 * 1024 * 1024:  # 20MB limit for videos
                            await bot.send_video(
                                chat_id=user_id,
                                video=open(file_path, 'rb'),
                                caption=caption,
                                parse_mode='Markdown'
                            )
                        else:
                            await bot.send_document(
                                chat_id=user_id,
                                document=open(file_path, 'rb'),
                                caption=caption,
                                parse_mode='Markdown'
                            )
                    else:
                        # All other files as documents
                        await bot.send_document(
                            chat_id=user_id,
                            document=open(file_path, 'rb'),
                            caption=caption,
                            parse_mode='Markdown'
                        )
                except Exception as file_error:
                    logger.error(f"Error sending file with specific method: {file_error}")
                    # Fallback to document for all file types
                    try:
                        await bot.send_document(
                            chat_id=user_id,
                            document=open(file_path, 'rb'),
                            caption=caption + "\n\n📝 *Sent as document for better compatibility*",
                            parse_mode='Markdown'
                        )
                    except Exception as doc_error:
                        logger.error(f"Even document fallback failed: {doc_error}")
                        # Last resort - send message only
                        await bot.send_message(
                            chat_id=user_id,
                            text=f"✅ *Conversion Complete but couldn't send file*\n\n"
                                 f"📁 *File:* {os.path.basename(file_path)}\n"
                                 f"📊 *Size:* {formatted_size}\n"
                                 f"💡 *Issue:* File is too large or format not supported by Telegram",
                            parse_mode='Markdown'
                        )
            else:
                # Send status update without file
                await bot.send_message(
                    chat_id=user_id,
                    text=status_message,
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Error sending professional status update to user {user_id}: {e}")
    
    async def send_ban_notification(self, user_id, job_id):
        """Send notification that job was cancelled due to ban"""
        try:
            from telegram import Bot
            bot = Bot(Config.BOT_TOKEN)
            
            await bot.send_message(
                chat_id=user_id,
                text="🚫 *Professional Conversion Cancelled*\n\n"
                     "Your conversion job has been cancelled because your account has been banned. "
                     "If you believe this is a mistake, please contact the administrator.",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error sending ban notification to user {user_id}: {e}")
    
    def add_to_history(self, job_data, output_path):
        """Add professional conversion to history"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO history 
                (user_id, input_type, output_type, input_size, output_size, success, conversion_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_data['user_id'],
                job_data['input_type'],
                job_data['output_format'],
                job_data['file_size'],
                os.path.getsize(output_path),
                True,
                0
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error adding to professional history: {e}")
    
    async def cleanup_files(self, file_path):
        """Cleanup temporary files"""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"🧹 Cleaned up professional conversion file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up professional files: {e}")

# Global professional queue manager instance
queue_manager = QueueManager()