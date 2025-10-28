import os
import asyncio
import subprocess
import tempfile
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class AudioConverter:
    def __init__(self):
        self.supported_formats = [
            'mp3', 'wav', 'ogg', 'flac', 'm4a', 'aac', 'aiff', 'amr', 
            'ape', 'mid', 'midi', 'aif', 'aifc', 'au', 'snd', 'ra', 'rm', 'voc', '8svx'
        ]
    
    async def convert_format(self, input_path, output_format):
        """Convert audio between formats using FFmpeg"""
        try:
            output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
            
            # FFmpeg command for audio conversion
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-y',  # Overwrite output
                '-loglevel', 'error',
                '-hide_banner',
            ]
            
            # Format-specific settings
            if output_format == 'mp3':
                cmd.extend(['-codec:a', 'libmp3lame', '-b:a', '192k', '-ar', '44100'])
            elif output_format == 'wav':
                cmd.extend(['-codec:a', 'pcm_s16le', '-ar', '44100', '-ac', '2'])
            elif output_format == 'ogg':
                cmd.extend(['-codec:a', 'libvorbis', '-b:a', '192k', '-ar', '44100'])
            elif output_format == 'flac':
                cmd.extend(['-codec:a', 'flac', '-compression_level', '8', '-ar', '44100'])
            elif output_format in ['m4a', 'aac']:
                cmd.extend(['-codec:a', 'aac', '-b:a', '192k', '-ar', '44100'])
            elif output_format in ['aiff', 'aif', 'aifc']:
                cmd.extend(['-codec:a', 'pcm_s16be', '-ar', '44100'])  # AIFF uses big-endian
            elif output_format == 'amr':
                cmd.extend(['-codec:a', 'libopencore_amrnb', '-ar', '8000', '-ac', '1'])
            elif output_format == 'mid' or output_format == 'midi':
                # For MIDI, we need a different approach - convert to WAV first if possible
                if not input_path.lower().endswith(('.mid', '.midi')):
                    raise Exception("MIDI conversion only supported from MIDI files")
                cmd.extend(['-codec:a', 'pcm_s16le', '-ar', '44100'])
            else:
                # Generic conversion
                cmd.extend(['-codec:a', 'copy'])
            
            cmd.append(output_path)
            
            logger.info(f"Running audio conversion: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
            
            if process.returncode == 0:
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    logger.info(f"Audio conversion successful: {input_path} -> {output_path}")
                    return output_path
                else:
                    raise Exception("Output file was created but is empty")
            else:
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Audio conversion failed"
                raise Exception(f"Audio conversion error: {error_msg}")
                
        except asyncio.TimeoutError:
            raise Exception("Audio conversion timeout - file may be too large")
        except Exception as e:
            raise Exception(f"Audio conversion failed: {str(e)}")
    
    async def compress_audio(self, input_path, quality='medium'):
        """Compress audio file"""
        try:
            output_path = input_path.rsplit('.', 1)[0] + '_compressed.mp3'
            
            quality_settings = {
                'low': '64k',
                'medium': '128k',
                'high': '192k'
            }
            
            bitrate = quality_settings.get(quality, '128k')
            
            cmd = [
                'ffmpeg', '-i', input_path,
                '-y',
                '-codec:a', 'libmp3lame',
                '-b:a', bitrate,
                '-ar', '44100',
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
                raise Exception("Audio compression failed")
                
        except Exception as e:
            raise Exception(f"Audio compression failed: {str(e)}")
    
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
            
            await asyncio.wait_for(process.communicate(), timeout=120)
            
            if process.returncode == 0:
                return cmd[-1]
            else:
                raise Exception("Audio trimming failed")
                
        except Exception as e:
            raise Exception(f"Audio trimming failed: {str(e)}")
    
    async def change_speed(self, input_path, speed_factor):
        """Change audio speed"""
        try:
            output_path = input_path.rsplit('.', 1)[0] + f'_speed_{speed_factor}.{input_path.split(".")[-1]}'
            
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-y',
                '-filter:a', f'atempo={speed_factor}',
                '-vn',
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await asyncio.wait_for(process.communicate(), timeout=120)
            
            if process.returncode == 0:
                return output_path
            else:
                raise Exception("Audio speed change failed")
                
        except Exception as e:
            raise Exception(f"Audio speed change failed: {str(e)}")

# Global converter instance
audio_converter = AudioConverter()