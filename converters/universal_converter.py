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
            
            # Get appropriate timeout based on file category
            input_category = self._get_file_category(job_data['input_type'])
            timeout = Config.get_conversion_timeout(input_category)
            
            # Perform conversion with professional settings
            try:
                output_path = await asyncio.wait_for(
                    self.perform_professional_conversion(job_data),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                raise Exception(f"Professional conversion timeout after {timeout} seconds")
            
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
    
    def _get_file_category(self, file_extension):
        """Get file category from extension"""
        file_extension = file_extension.lower()
        
        for category, extensions in Config.SUPPORTED_FORMATS.items():
            if file_extension in extensions:
                return category
        return 'document'  # Default category
    
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
            output_path = await universal_converter.convert_file(input_path, output_format, input_extension)
            
            # Verify the output file is valid
            if not output_path or not os.path.exists(output_path):
                raise Exception("Conversion failed - no output file created")
                
            output_size = os.path.getsize(output_path)
            if output_size == 0:
                raise Exception("Conversion produced empty file")
                
            logger.info(f"Conversion successful: {output_path} ({output_size} bytes)")
            return output_path
                
        except Exception as e:
            logger.error(f"Professional conversion error for job {job_data['job_id']}: {e}")
            raise
    
    async def send_status_update(self, user_id, job_id, message, progress, details="", file_path=None):
        """Send professional status update to user with proper large file handling"""
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
                # Get file info
                file_size = os.path.getsize(file_path)
                file_ext = file_path.split('.')[-1].upper()
                formatted_size = format_file_size(file_size)
                file_size_mb = file_size // (1024 * 1024)
                
                caption = f"✅ *Professional Conversion Complete!*\n\n"
                caption += f"📁 *Format:* {file_ext}\n"
                caption += f"📊 *Size:* {formatted_size}\n"
                caption += f"🎯 *Quality:* Professional Grade\n"
                
                try:
                    # For audio files, always try audio method first for better user experience
                    if file_ext in ['MP3', 'WAV', 'AAC', 'OGG']:
                        if file_size <= 50 * 1024 * 1024:  # 50MB limit for audio
                            await bot.send_audio(
                                chat_id=user_id,
                                audio=open(file_path, 'rb'),
                                caption=caption,
                                parse_mode='Markdown'
                            )
                            return
                        else:
                            # Large audio file, send as document with explanation
                            caption += f"\n📦 *Large audio file - sent as document*\n"
                            caption += f"💡 *Tip:* For better audio quality, try converting to MP3 with lower bitrate"
                    
                    # For very large files (>500MB), always use document method
                    if file_size > 500 * 1024 * 1024:
                        caption += f"\n📦 *Large file - sent as document*"
                        await bot.send_document(
                            chat_id=user_id,
                            document=open(file_path, 'rb'),
                            caption=caption,
                            parse_mode='Markdown'
                        )
                    elif file_ext in ['JPG', 'JPEG', 'PNG', 'WEBP', 'BMP'] and file_size < 10 * 1024 * 1024:
                        # Small images as photos
                        await bot.send_photo(
                            chat_id=user_id,
                            photo=open(file_path, 'rb'),
                            caption=caption,
                            parse_mode='Markdown'
                        )
                    elif file_ext == 'GIF':
                        # GIFs as documents to preserve animation
                        await bot.send_document(
                            chat_id=user_id,
                            document=open(file_path, 'rb'),
                            caption=caption,
                            parse_mode='Markdown'
                        )
                    elif file_ext in ['MP4', 'AVI', 'MOV', 'MKV'] and file_size < 50 * 1024 * 1024:
                        # Video files under 50MB
                        await bot.send_video(
                            chat_id=user_id,
                            video=open(file_path, 'rb'),
                            caption=caption,
                            parse_mode='Markdown'
                        )
                    else:
                        # Everything else as documents (supports up to 2GB)
                        await bot.send_document(
                            chat_id=user_id,
                            document=open(file_path, 'rb'),
                            caption=caption,
                            parse_mode='Markdown'
                        )
                        
                except Exception as file_error:
                    logger.error(f"Error sending file with specific method: {file_error}")
                    # Universal fallback - document method supports largest files
                    try:
                        await bot.send_document(
                            chat_id=user_id,
                            document=open(file_path, 'rb'),
                            caption=caption + "\n\n📦 *Sent as document for maximum compatibility*",
                            parse_mode='Markdown'
                        )
                    except Exception as doc_error:
                        logger.error(f"Document fallback failed: {doc_error}")
                        # If even document fails, the file might be corrupted or too large
                        # Try to get more info about the file
                        file_info = f"Format: {file_ext}, Size: {formatted_size}"
                        if not os.path.exists(file_path):
                            file_info += ", File not found"
                        elif os.path.getsize(file_path) == 0:
                            file_info += ", File is empty"
                        
                        await bot.send_message(
                            chat_id=user_id,
                            text=f"✅ *Conversion Complete!*\n\n"
                                 f"📁 *File:* {os.path.basename(file_path)}\n"
                                 f"{file_info}\n\n"
                                 f"⚠️ *Could not send file via Telegram*\n"
                                 f"The file was converted successfully but couldn't be delivered.\n\n"
                                 f"💡 *Possible solutions:*\n"
                                 f"• Try converting to a different format\n"
                                 f"• The file might be too large for Telegram\n"
                                 f"• Try a smaller input file\n"
                                 f"• Contact support if this persists",
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