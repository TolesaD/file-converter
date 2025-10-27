import os
import asyncio
import subprocess
import tempfile
from pathlib import Path

class AudioConverter:
    def __init__(self):
        self.supported_formats = ['mp3', 'wav', 'ogg', 'flac', 'm4a', 'aac']
    
    async def convert_format(self, input_path, output_format):
        """Convert audio between formats with multiple fallback methods"""
        try:
            # Method 1: Try pydub first
            return await self._convert_with_pydub(input_path, output_format)
        except Exception as e:
            logger.warning(f"Pydub conversion failed: {e}, trying ffmpeg directly...")
            try:
                # Method 2: Try direct ffmpeg
                return await self._convert_with_ffmpeg(input_path, output_format)
            except Exception as e2:
                logger.warning(f"FFmpeg conversion failed: {e2}, trying system commands...")
                # Method 3: Try system audio conversion tools
                return await self._convert_with_system_tools(input_path, output_format)
    
    async def _convert_with_pydub(self, input_path, output_format):
        """Convert using pydub (requires ffmpeg)"""
        try:
            from pydub import AudioSegment
            
            # Load audio file
            audio = AudioSegment.from_file(input_path)
            
            output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
            
            # Format-specific parameters
            export_params = {}
            if output_format == 'mp3':
                export_params = {'format': 'mp3', 'bitrate': '192k'}
            elif output_format == 'wav':
                export_params = {'format': 'wav'}
            elif output_format == 'ogg':
                export_params = {'format': 'ogg', 'bitrate': '192k'}
            elif output_format == 'flac':
                export_params = {'format': 'flac'}
            elif output_format in ['m4a', 'aac']:
                export_params = {'format': 'ipod', 'bitrate': '192k'}
            else:
                export_params = {'format': output_format}
            
            # Export with timeout
            await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: audio.export(output_path, **export_params)
                ),
                timeout=120  # 2 minute timeout
            )
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return output_path
            else:
                raise Exception("Output file not created or empty")
                
        except asyncio.TimeoutError:
            raise Exception("Audio conversion timeout - file may be too large")
        except Exception as e:
            raise Exception(f"Pydub conversion error: {str(e)}")
    
    async def _convert_with_ffmpeg(self, input_path, output_format):
        """Convert using direct ffmpeg command"""
        try:
            output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
            
            # FFmpeg command for audio conversion
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-y',  # Overwrite output file
                '-loglevel', 'error',  # Only show errors
            ]
            
            # Add format-specific options
            if output_format == 'mp3':
                cmd.extend(['-codec:a', 'libmp3lame', '-b:a', '192k'])
            elif output_format == 'wav':
                cmd.extend(['-codec:a', 'pcm_s16le'])
            elif output_format == 'ogg':
                cmd.extend(['-codec:a', 'libvorbis', '-b:a', '192k'])
            elif output_format == 'flac':
                cmd.extend(['-codec:a', 'flac'])
            elif output_format in ['m4a', 'aac']:
                cmd.extend(['-codec:a', 'aac', '-b:a', '192k'])
            
            cmd.append(output_path)
            
            # Run with timeout
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
            
            if process.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                error_msg = stderr.decode() if stderr else "Unknown ffmpeg error"
                raise Exception(f"FFmpeg failed: {error_msg}")
                
        except asyncio.TimeoutError:
            raise Exception("FFmpeg conversion timeout")
        except Exception as e:
            raise Exception(f"FFmpeg conversion error: {str(e)}")
    
    async def _convert_with_system_tools(self, input_path, output_format):
        """Convert using system audio tools as last resort"""
        try:
            output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
            
            # Try different system tools based on availability
            if self._check_tool('avconv'):
                cmd = ['avconv', '-i', input_path, output_path]
            elif self._check_tool('sox'):
                cmd = ['sox', input_path, output_path]
            else:
                raise Exception("No audio conversion tools available")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
            
            if process.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                raise Exception("System tool conversion failed")
                
        except asyncio.TimeoutError:
            raise Exception("System tool conversion timeout")
        except Exception as e:
            raise Exception(f"System tool conversion error: {str(e)}")
    
    async def compress_audio(self, input_path, bitrate='128k'):
        """Compress audio file"""
        try:
            output_path = input_path.rsplit('.', 1)[0] + '_compressed.mp3'
            
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-y',
                '-codec:a', 'libmp3lame',
                '-b:a', bitrate,
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
            
            if process.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                raise Exception("Audio compression failed")
                
        except Exception as e:
            raise Exception(f"Audio compression failed: {str(e)}")
    
    async def extract_audio(self, video_path, output_format='mp3'):
        """Extract audio from video file"""
        try:
            output_path = video_path.rsplit('.', 1)[0] + f'_audio.{output_format}'
            
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-y',
                '-vn',  # No video
                '-acodec', 'copy' if output_format == 'm4a' else 'libmp3lame',
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=180)
            
            if process.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                raise Exception("Audio extraction failed")
                
        except Exception as e:
            raise Exception(f"Audio extraction failed: {str(e)}")
    
    async def trim_audio(self, input_path, start_time, end_time):
        """Trim audio file"""
        try:
            duration = end_time - start_time
            
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-y',
                '-ss', str(start_time),
                '-t', str(duration),
                '-acodec', 'copy',
                input_path.rsplit('.', 1)[0] + f'_trimmed.{input_path.split(".")[-1]}'
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
            
            if process.returncode == 0:
                return cmd[-1]
            else:
                raise Exception("Audio trimming failed")
                
        except Exception as e:
            raise Exception(f"Audio trimming failed: {str(e)}")
    
    async def change_speed(self, input_path, speed_factor):
        """Change audio speed"""
        try:
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-y',
                '-filter:a', f'atempo={speed_factor}',
                '-vn',
                input_path.rsplit('.', 1)[0] + f'_speed_{speed_factor}.{input_path.split(".")[-1]}'
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
            
            if process.returncode == 0:
                return cmd[-1]
            else:
                raise Exception("Audio speed change failed")
                
        except Exception as e:
            raise Exception(f"Audio speed change failed: {str(e)}")
    
    def _check_tool(self, tool_name):
        """Check if a command-line tool is available"""
        try:
            result = subprocess.run([tool_name, '--version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

# Global converter instance
audio_converter = AudioConverter()