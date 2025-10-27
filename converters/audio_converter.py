import os
import asyncio
import subprocess

class AudioConverter:
    def __init__(self):
        self.supported_formats = ['mp3', 'wav', 'ogg', 'flac', 'm4a', 'aac']
    
    async def convert_format(self, input_path, output_format):
        """Convert audio between formats using pydub or ffmpeg"""
        try:
            from pydub import AudioSegment
            
            # Load audio file
            audio = AudioSegment.from_file(input_path)
            
            output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
            
            # Format-specific parameters
            if output_format == 'mp3':
                audio.export(output_path, format='mp3', bitrate='192k')
            elif output_format == 'wav':
                audio.export(output_path, format='wav')
            elif output_format == 'ogg':
                audio.export(output_path, format='ogg', bitrate='192k')
            elif output_format == 'flac':
                audio.export(output_path, format='flac')
            elif output_format in ['m4a', 'aac']:
                audio.export(output_path, format='ipod', bitrate='192k')
            else:
                audio.export(output_path, format=output_format)
            
            return output_path
        except Exception as e:
            # Fallback to ffmpeg
            return await self._ffmpeg_convert(input_path, output_format)
    
    async def compress_audio(self, input_path, bitrate='128k'):
        """Compress audio file"""
        try:
            from pydub import AudioSegment
            
            audio = AudioSegment.from_file(input_path)
            output_path = input_path.rsplit('.', 1)[0] + '_compressed.mp3'
            
            # Compress to lower bitrate
            audio.export(output_path, format='mp3', bitrate=bitrate)
            
            return output_path
        except Exception as e:
            raise Exception(f"Audio compression failed: {str(e)}")
    
    async def extract_audio(self, video_path, output_format='mp3'):
        """Extract audio from video file"""
        try:
            from pydub import AudioSegment
            
            # Load video and extract audio
            video = AudioSegment.from_file(video_path, "mp4")
            output_path = video_path.rsplit('.', 1)[0] + f'_audio.{output_format}'
            
            video.export(output_path, format=output_format)
            return output_path
        except Exception as e:
            raise Exception(f"Audio extraction failed: {str(e)}")
    
    async def trim_audio(self, input_path, start_time, end_time):
        """Trim audio file"""
        try:
            from pydub import AudioSegment
            
            audio = AudioSegment.from_file(input_path)
            
            # Convert times to milliseconds
            start_ms = start_time * 1000
            end_ms = end_time * 1000
            
            # Trim audio
            trimmed_audio = audio[start_ms:end_ms]
            output_path = input_path.rsplit('.', 1)[0] + f'_trimmed.{input_path.split(".")[-1]}'
            
            trimmed_audio.export(output_path, format=input_path.split('.')[-1])
            return output_path
        except Exception as e:
            raise Exception(f"Audio trimming failed: {str(e)}")
    
    async def change_speed(self, input_path, speed_factor):
        """Change audio speed"""
        try:
            # Use ffmpeg for speed change
            output_path = input_path.rsplit('.', 1)[0] + f'_speed_{speed_factor}.{input_path.split(".")[-1]}'
            
            cmd = [
                'ffmpeg', '-i', input_path,
                '-filter:a', f'atempo={speed_factor}',
                '-vn', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                raise Exception("FFmpeg speed change failed")
        except Exception as e:
            raise Exception(f"Audio speed change failed: {str(e)}")
    
    async def _ffmpeg_convert(self, input_path, output_format):
        """Fallback conversion using ffmpeg"""
        try:
            output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
            
            cmd = ['ffmpeg', '-i', input_path, '-y', output_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                raise Exception("FFmpeg conversion failed")
        except Exception as e:
            raise Exception(f"FFmpeg conversion failed: {str(e)}")

# Global converter instance
audio_converter = AudioConverter()