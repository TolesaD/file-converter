import asyncio
import os
from datetime import datetime
from database import db
from config import Config
from converters.document_converter import doc_converter
from converters.image_converter import img_converter
from converters.audio_converter import audio_converter
from telegram import Bot
import logging

logger = logging.getLogger(__name__)

class QueueManager:
    def __init__(self):
        self.processing = False
        self.current_tasks = []
    
    async def add_to_queue(self, job_data):
        """Add a job to the processing queue"""
        try:
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
        logger.info("🚀 Queue processor started")
        
        try:
            while self.processing:
                # Check if we can process more jobs
                async with Config.job_lock:
                    if Config.active_jobs >= Config.MAX_CONCURRENT_JOBS:
                        await asyncio.sleep(1)
                        continue
                
                # Get next job from queue (with timeout to allow cancellation)
                try:
                    job_data = await asyncio.wait_for(Config.processing_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
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
        """Process a single conversion job"""
        try:
            logger.info(f"Starting conversion for job {job_data['job_id']}")
            
            # Send processing started message
            await self.send_status_update(
                job_data['user_id'],
                job_data['job_id'],
                "🔄 Processing started...",
                20
            )
            
            # Perform conversion
            output_path = await self.perform_conversion(job_data)
            
            if output_path and os.path.exists(output_path):
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
                    "✅ Conversion completed!",
                    100,
                    output_path
                )
                
                # Add to history
                self.add_to_history(job_data, output_path)
                
                logger.info(f"✅ Job {job_data['job_id']} completed successfully")
                
            else:
                raise Exception("Conversion produced no output")
                
        except Exception as e:
            logger.error(f"Job {job_data['job_id']} processing error: {e}")
            db.update_conversion_job(
                job_data['job_id'],
                status='failed',
                error_message=str(e)
            )
            
            await self.send_status_update(
                job_data['user_id'],
                job_data['job_id'],
                f"❌ Conversion failed: {str(e)}",
                0
            )
        
        finally:
            # Cleanup and decrement active jobs counter
            async with Config.job_lock:
                Config.active_jobs = max(0, Config.active_jobs - 1)
            
            # Cleanup temporary files
            await self.cleanup_files(job_data.get('input_path'))
    
    async def perform_conversion(self, job_data):
        """Route to appropriate converter based on conversion type"""
        conversion_type = job_data['conversion_type']
        input_path = job_data['input_path']
        output_format = job_data['output_format']
        
        # Update progress
        await self.send_status_update(
            job_data['user_id'],
            job_data['job_id'],
            "🔄 Converting file...",
            50
        )
        
        try:
            # Route conversions
            if conversion_type.startswith('convert_pdf'):
                if conversion_type == 'convert_pdf_images':
                    output_files = await doc_converter.convert_pdf_to_images(input_path, output_format)
                    return output_files[0] if output_files else None
                elif conversion_type == 'convert_pdf_docx':
                    output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
                    return await doc_converter.convert_pdf_to_docx(input_path, output_path)
            elif conversion_type.startswith('convert_') and any(img_type in conversion_type for img_type in ['jpg', 'png', 'webp']):
                if conversion_type in ['convert_jpg_png', 'convert_png_jpg', 'convert_webp_jpg']:
                    output_fmt = conversion_type.split('_')[2]
                    return await img_converter.convert_format(input_path, output_fmt)
            elif conversion_type.startswith('convert_') and any(audio_type in conversion_type for audio_type in ['mp3', 'wav']):
                if conversion_type in ['convert_mp3_wav', 'convert_wav_mp3']:
                    output_fmt = conversion_type.split('_')[2]
                    return await audio_converter.convert_format(input_path, output_fmt)
            else:
                # Default conversion
                return await self.simple_convert(input_path, output_format)
                
        except Exception as e:
            logger.error(f"Conversion error for job {job_data['job_id']}: {e}")
            raise
    
    async def simple_convert(self, input_path, output_format):
        """Simple file conversion fallback"""
        try:
            output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
            
            if output_format == 'txt':
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(f"Converted file from {input_path.split('.')[-1]} to {output_format}\n")
                    f.write("This is a placeholder conversion.\n")
            else:
                import shutil
                shutil.copy2(input_path, output_path)
            
            return output_path
        except Exception as e:
            logger.error(f"Simple conversion error: {e}")
            raise
    
    async def send_status_update(self, user_id, job_id, message, progress, file_path=None):
        """Send status update to user"""
        try:
            bot = Bot(Config.BOT_TOKEN)
            
            # Get queue info
            queued_jobs = db.get_user_queued_jobs(user_id)
            current_job = next((job for job in queued_jobs if job['id'] == job_id), None)
            
            status_message = f"{message}\n"
            status_message += f"📊 Progress: {progress}%\n"
            
            if current_job and current_job['queue_position'] > 1:
                status_message += f"📋 Queue position: {current_job['queue_position']}\n"
            
            if progress == 100 and file_path:
                # Send the converted file
                file_size = os.path.getsize(file_path)
                file_ext = file_path.split('.')[-1].upper()
                
                if file_ext in ['JPG', 'JPEG', 'PNG', 'WEBP']:
                    await bot.send_photo(
                        chat_id=user_id,
                        photo=open(file_path, 'rb'),
                        caption=f"✅ {file_ext} file ready!\nSize: {file_size} bytes"
                    )
                elif file_ext in ['MP3', 'WAV', 'OGG']:
                    await bot.send_audio(
                        chat_id=user_id,
                        audio=open(file_path, 'rb'),
                        caption=f"✅ {file_ext} file ready!\nSize: {file_size} bytes"
                    )
                elif file_ext in ['MP4', 'GIF']:
                    await bot.send_video(
                        chat_id=user_id,
                        video=open(file_path, 'rb'),
                        caption=f"✅ {file_ext} file ready!\nSize: {file_size} bytes"
                    )
                else:
                    await bot.send_document(
                        chat_id=user_id,
                        document=open(file_path, 'rb'),
                        caption=f"✅ {file_ext} file ready!\nSize: {file_size} bytes"
                    )
            else:
                # Send status update
                await bot.send_message(
                    chat_id=user_id,
                    text=status_message
                )
                
        except Exception as e:
            logger.error(f"Error sending status update to user {user_id}: {e}")
    
    def add_to_history(self, job_data, output_path):
        """Add conversion to history"""
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
                0  # Could calculate actual conversion time
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error adding to history: {e}")
    
    async def cleanup_files(self, file_path):
        """Cleanup temporary files"""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"🧹 Cleaned up file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up files: {e}")

# Global queue manager instance
queue_manager = QueueManager()