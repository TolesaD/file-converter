import os
import asyncio
import logging
from pydub import AudioSegment
import aiofiles

logger = logging.getLogger(__name__)

class AudioConverter:
    def __init__(self):
        self.supported_formats = ['mp3', 'wav', 'ogg', 'flac', 'm4a', 'aac']
    
    async def convert_format(self, input_path: str, output_format: str) -> str:
        """Convert audio to different format using pydub"""
        try:
            output_path = os.path.splitext(input_path)[0] + f'_converted.{output_format}'
            
            # Load audio file
            audio = AudioSegment.from_file(input_path)
            
            # Export to target format
            if output_format == 'mp3':
                audio.export(output_path, format='mp3', bitrate='192k')
            elif output_format == 'wav':
                audio.export(output_path, format='wav')
            elif output_format == 'ogg':
                audio.export(output_path, format='ogg', codec='libvorbis')
            elif output_format == 'flac':
                audio.export(output_path, format='flac')
            elif output_format == 'm4a':
                audio.export(output_path, format='ipod', codec='aac')
            elif output_format == 'aac':
                audio.export(output_path, format='adts', codec='aac')
            else:
                audio.export(output_path, format=output_format)
            
            return output_path
                
        except Exception as e:
            logger.error(f"Audio conversion error: {e}")
            # Fallback to FFmpeg
            return await self._convert_with_ffmpeg(input_path, output_format)
    
    async def _convert_with_ffmpeg(self, input_path: str, output_format: str) -> str:
        """Convert using FFmpeg as fallback"""
        try:
            output_path = os.path.splitext(input_path)[0] + f'_converted.{output_format}'
            
            cmd = ['ffmpeg', '-i', input_path, '-y', output_path]
            
            # Add format-specific options
            if output_format == 'mp3':
                cmd.extend(['-codec:a', 'libmp3lame', '-b:a', '192k'])
            elif output_format == 'ogg':
                cmd.extend(['-codec:a', 'libvorbis', '-q:a', '4'])
            
            await self._run_command(cmd)
            
            if os.path.exists(output_path):
                return output_path
            else:
                raise Exception("Audio conversion failed - output not found")
                
        except Exception as e:
            logger.error(f"FFmpeg audio conversion error: {e}")
            raise Exception(f"Audio to {output_format} conversion failed")
    
    async def compress_audio(self, input_path: str) -> str:
        """Compress audio file"""
        output_path = os.path.splitext(input_path)[0] + '_compressed.mp3'
        
        try:
            audio = AudioSegment.from_file(input_path)
            audio.export(output_path, format='mp3', bitrate='128k')
            return output_path
        except Exception as e:
            # Fallback to FFmpeg
            cmd = [
                'ffmpeg', '-i', input_path, '-y',
                '-codec:a', 'libmp3lame', '-b:a', '128k',
                output_path
            ]
            await self._run_command(cmd)
            return output_path
    
    async def trim_audio(self, input_path: str, start_time: str, end_time: str) -> str:
        """Trim audio file"""
        output_path = os.path.splitext(input_path)[0] + '_trimmed.mp3'
        
        try:
            # Convert time strings to milliseconds
            start_ms = self._time_to_ms(start_time)
            end_ms = self._time_to_ms(end_time)
            
            audio = AudioSegment.from_file(input_path)
            trimmed = audio[start_ms:end_ms]
            trimmed.export(output_path, format='mp3')
            return output_path
        except Exception as e:
            # Fallback to FFmpeg
            cmd = [
                'ffmpeg', '-i', input_path, '-y',
                '-ss', start_time, '-to', end_time,
                '-codec', 'copy', output_path
            ]
            await self._run_command(cmd)
            return output_path
    
    async def change_speed(self, input_path: str, speed: float) -> str:
        """Change audio speed"""
        output_path = os.path.splitext(input_path)[0] + f'_speed_{speed}.mp3'
        
        cmd = [
            'ffmpeg', '-i', input_path, '-y',
            '-filter:a', f'atempo={speed}',
            output_path
        ]
        
        await self._run_command(cmd)
        return output_path
    
    def _time_to_ms(self, time_str: str) -> int:
        """Convert time string (HH:MM:SS) to milliseconds"""
        parts = time_str.split(':')
        if len(parts) == 3:
            h, m, s = parts
            return (int(h) * 3600 + int(m) * 60 + float(s)) * 1000
        elif len(parts) == 2:
            m, s = parts
            return (int(m) * 60 + float(s)) * 1000
        else:
            return float(time_str) * 1000
    
    async def _run_command(self, cmd: list) -> str:
        """Run system command"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise Exception(f"Command failed: {error_msg}")
            
            return stdout.decode() if stdout else ""
            
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            raise Exception(f"Conversion failed: {str(e)}")

# Global instance
audio_converter = AudioConverter()