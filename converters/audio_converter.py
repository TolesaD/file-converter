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
            'ape', 'mid', 'midi', 'aif', 'aifc', 'au', 'snd', 'ra', 'rm', 'voc'
        ]
    
    async def convert_format(self, input_path, output_format):
        """Convert audio between formats with robust error handling"""
        try:
            # Always use ffmpeg for reliability
            return await self._convert_with_ffmpeg(input_path, output_format)
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            raise Exception(f"Audio conversion failed: {str(e)}")
    
    async def _convert_with_ffmpeg(self, input_path, output_format):
        """Convert using direct ffmpeg command - most reliable"""
        try:
            output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
            
            # Basic ffmpeg command
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-y',  # Overwrite output file
                '-loglevel', 'error',  # Only show errors
                '-hide_banner',
            ]
            
            # Add format-specific options
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
            else:
                # Generic conversion
                cmd.extend(['-codec:a', 'copy'])  # Try to copy without re-encoding if possible
            
            cmd.append(output_path)
            
            logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
            
            # Run with timeout
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
            
            if process.returncode == 0:
                # Verify output file was created and has content
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    logger.info(f"Audio conversion successful: {input_path} -> {output_path}")
                    return output_path
                else:
                    raise Exception("Output file was created but is empty")
            else:
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Unknown ffmpeg error"
                logger.error(f"FFmpeg failed with error: {error_msg}")
                raise Exception(f"Audio conversion failed: {error_msg}")
                
        except asyncio.TimeoutError:
            logger.error("Audio conversion timeout")
            raise Exception("Audio conversion timeout - file may be too large or corrupted")
        except Exception as e:
            logger.error(f"FFmpeg conversion error: {str(e)}")
            raise Exception(f"Audio conversion error: {str(e)}")
    
    async def compress_audio(self, input_path, bitrate='128k'):
        """Compress audio file"""
        try:
            output_path = input_path.rsplit('.', 1)[0] + '_compressed.mp3'
            
            cmd = [
                'ffmpeg', '-i', input_path,
                '-y', '-codec:a', 'libmp3lame',
                '-b:a', bitrate, '-ar', '44100',
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

# Global converter instance
audio_converter = AudioConverter()