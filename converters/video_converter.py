import os
import asyncio
import subprocess
import tempfile
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class VideoConverter:
    def __init__(self):
        self.supported_formats = [
            'mp4', 'avi', 'wmv', 'mkv', '3gp', '3gpp', 'mpg', 'mpeg', 
            'webm', 'ts', 'mov', 'flv', 'asf', 'vob', 'm4v', 'rmvb',
            'ogv', 'qt', 'm2ts', 'mts', 'f4v', 'mxf', 'divx', 'xvid'
        ]
    
    async def convert_format(self, input_path, output_format):
        """Convert video between formats using FFmpeg - WORKING VERSION"""
        try:
            logger.info(f"Starting video conversion: {input_path} -> {output_format}")
            
            # Special handling for GIF
            if output_format.lower() == 'gif':
                return await self.create_gif(input_path)
            
            output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
            
            # Base FFmpeg command
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-y',  # Overwrite output
                '-loglevel', 'error',
                '-hide_banner',
            ]
            
            # Add format-specific options
            if output_format == 'mp4':
                cmd.extend([
                    '-c:v', 'libx264', 
                    '-preset', 'medium',
                    '-crf', '23',
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    '-movflags', '+faststart'
                ])
            elif output_format == 'webm':
                cmd.extend([
                    '-c:v', 'libvpx-vp9',
                    '-b:v', '1M',
                    '-c:a', 'libvorbis',
                    '-b:a', '128k'
                ])
            elif output_format == 'avi':
                cmd.extend([
                    '-c:v', 'mpeg4',
                    '-qscale:v', '3',
                    '-c:a', 'mp3',
                    '-b:a', '128k'
                ])
            elif output_format == 'mov':
                cmd.extend([
                    '-c:v', 'libx264',
                    '-preset', 'medium',
                    '-c:a', 'aac',
                    '-b:a', '128k'
                ])
            elif output_format == 'mkv':
                cmd.extend([
                    '-c:v', 'libx264',
                    '-c:a', 'aac'
                ])
            elif output_format == 'wmv':
                cmd.extend([
                    '-c:v', 'wmv2',
                    '-c:a', 'wmav2'
                ])
            else:
                # Generic conversion - try to copy when possible
                cmd.extend(['-c', 'copy'])
            
            cmd.append(output_path)
            
            logger.info(f"Running FFmpeg: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
            
            if process.returncode == 0:
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    logger.info(f"Video conversion successful: {output_path}")
                    return output_path
                else:
                    raise Exception("Output file created but is empty")
            else:
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Unknown error"
                logger.error(f"FFmpeg failed: {error_msg}")
                raise Exception(f"Video conversion failed: {error_msg}")
                
        except asyncio.TimeoutError:
            raise Exception("Video conversion timeout - file may be too large")
        except Exception as e:
            logger.error(f"Video conversion error: {str(e)}")
            raise Exception(f"Video conversion failed: {str(e)}")
    
    async def create_gif(self, input_path, duration=5):
        """Create GIF from video - WORKING VERSION"""
        try:
            output_path = input_path.rsplit('.', 1)[0] + '.gif'
            
            # First, get video duration to avoid empty GIFs
            probe_cmd = [
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                input_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *probe_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            video_duration = float(stdout.decode().strip()) if stdout else 10
            
            # Use shorter duration if video is short
            actual_duration = min(duration, video_duration)
            
            # Create GIF with proper parameters
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-y',
                '-t', str(actual_duration),  # Duration in seconds
                '-vf', 'fps=10,scale=480:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse',
                '-loop', '0',  # Infinite loop
                output_path
            ]
            
            logger.info(f"Creating GIF: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await asyncio.wait_for(process.communicate(), timeout=120)
            
            if process.returncode == 0 and os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                if file_size > 1000:  # Ensure GIF is not empty
                    logger.info(f"GIF created successfully: {output_path} ({file_size} bytes)")
                    return output_path
                else:
                    raise Exception("GIF file is too small (likely empty)")
            else:
                raise Exception("GIF creation failed")
                
        except Exception as e:
            logger.error(f"GIF creation error: {str(e)}")
            raise Exception(f"GIF creation failed: {str(e)}")
    
    async def compress_video(self, input_path, quality='medium'):
        """Compress video file"""
        try:
            output_path = input_path.rsplit('.', 1)[0] + '_compressed.mp4'
            
            quality_settings = {
                'low': '500k',
                'medium': '1000k', 
                'high': '2000k'
            }
            
            bitrate = quality_settings.get(quality, '1000k')
            
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-y',
                '-c:v', 'libx264',
                '-b:v', bitrate,
                '-preset', 'medium',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-movflags', '+faststart',
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await asyncio.wait_for(process.communicate(), timeout=300)
            
            if process.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                raise Exception("Video compression failed")
                
        except Exception as e:
            raise Exception(f"Video compression failed: {str(e)}")
    
    async def extract_audio(self, video_path, output_format='mp3'):
        """Extract audio from video"""
        try:
            output_path = video_path.rsplit('.', 1)[0] + f'_audio.{output_format}'
            
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-y',
                '-vn',  # No video
                '-acodec', 'libmp3lame' if output_format == 'mp3' else 'copy',
                '-b:a', '192k' if output_format == 'mp3' else None,
                output_path
            ]
            
            # Remove None values
            cmd = [arg for arg in cmd if arg is not None]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await asyncio.wait_for(process.communicate(), timeout=180)
            
            if process.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                raise Exception("Audio extraction failed")
                
        except Exception as e:
            raise Exception(f"Audio extraction failed: {str(e)}")
    
    async def trim_video(self, input_path, start_time, end_time):
        """Trim video file"""
        try:
            duration = end_time - start_time
            
            output_path = input_path.rsplit('.', 1)[0] + f'_trimmed.{input_path.split(".")[-1]}'
            
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-y',
                '-ss', str(start_time),
                '-t', str(duration),
                '-c', 'copy',  # Copy without re-encoding
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await asyncio.wait_for(process.communicate(), timeout=180)
            
            if process.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                raise Exception("Video trimming failed")
                
        except Exception as e:
            raise Exception(f"Video trimming failed: {str(e)}")

# Global converter instance
video_converter = VideoConverter()