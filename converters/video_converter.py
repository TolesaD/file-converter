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
        """Convert video between formats using FFmpeg"""
        try:
            output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
            
            # Basic FFmpeg command for video conversion
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-y',  # Overwrite output
                '-loglevel', 'error',
                '-hide_banner',
            ]
            
            # Add format-specific options
            if output_format == 'mp4':
                cmd.extend(['-c:v', 'libx264', '-c:a', 'aac', '-movflags', '+faststart'])
            elif output_format == 'webm':
                cmd.extend(['-c:v', 'libvpx-vp9', '-c:a', 'libvorbis'])
            elif output_format == 'avi':
                cmd.extend(['-c:v', 'mpeg4', '-c:a', 'mp3'])
            elif output_format == 'mov':
                cmd.extend(['-c:v', 'libx264', '-c:a', 'aac'])
            elif output_format == 'mkv':
                cmd.extend(['-c:v', 'libx264', '-c:a', 'aac'])
            elif output_format == 'gif':
                return await self.create_gif(input_path)
            else:
                # Generic conversion - copy codecs when possible
                cmd.extend(['-c', 'copy'])
            
            cmd.append(output_path)
            
            logger.info(f"Running video conversion: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
            
            if process.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Video conversion failed"
                raise Exception(f"Video conversion error: {error_msg}")
                
        except asyncio.TimeoutError:
            raise Exception("Video conversion timeout - file may be too large")
        except Exception as e:
            raise Exception(f"Video conversion failed: {str(e)}")
    
    async def create_gif(self, input_path, duration=10):
        """Create GIF from video"""
        try:
            output_path = input_path.rsplit('.', 1)[0] + '.gif'
            
            # Extract a portion of the video and convert to GIF
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-y',
                '-t', str(duration),  # Duration in seconds
                '-vf', 'fps=10,scale=320:-1:flags=lanczos',
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await asyncio.wait_for(process.communicate(), timeout=120)
            
            if process.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                raise Exception("GIF creation failed")
                
        except Exception as e:
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
                '-c:a', 'aac',
                '-b:a', '128k',
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
                raise Exception("Audio extraction failed")
                
        except Exception as e:
            raise Exception(f"Audio extraction failed: {str(e)}")
    
    async def trim_video(self, input_path, start_time, end_time):
        """Trim video file"""
        try:
            duration = end_time - start_time
            
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-y',
                '-ss', str(start_time),
                '-t', str(duration),
                '-c', 'copy',  # Copy without re-encoding
                input_path.rsplit('.', 1)[0] + f'_trimmed.{input_path.split(".")[-1]}'
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await asyncio.wait_for(process.communicate(), timeout=180)
            
            if process.returncode == 0:
                return cmd[-1]
            else:
                raise Exception("Video trimming failed")
                
        except Exception as e:
            raise Exception(f"Video trimming failed: {str(e)}")

# Global converter instance
video_converter = VideoConverter()