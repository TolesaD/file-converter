import os
import asyncio
import logging
import subprocess

logger = logging.getLogger(__name__)

class VideoConverter:
    def __init__(self):
        self.supported_formats = ['mp4', 'avi', 'mkv', 'mov', 'webm', 'wmv', 'flv', 'gif']
    
    async def convert_format(self, input_path: str, output_format: str) -> str:
        """Convert video to different format"""
        try:
            output_path = os.path.splitext(input_path)[0] + f'_converted.{output_format}'
            
            # Try moviepy first for better quality
            try:
                from moviepy.editor import VideoFileClip
                
                clip = VideoFileClip(input_path)
                if output_format == 'gif':
                    clip.write_gif(output_path, fps=10)
                else:
                    clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
                clip.close()
                return output_path
            except ImportError:
                pass
            
            # Fallback to FFmpeg
            cmd = ['ffmpeg', '-i', input_path, '-y', output_path]
            
            # Add format-specific options
            if output_format == 'mp4':
                cmd.extend(['-codec:v', 'libx264', '-codec:a', 'aac'])
            elif output_format == 'webm':
                cmd.extend(['-codec:v', 'libvpx-vp9', '-codec:a', 'libvorbis'])
            elif output_format == 'avi':
                cmd.extend(['-codec:v', 'mpeg4', '-codec:a', 'mp3'])
            
            await self._run_command(cmd)
            
            if os.path.exists(output_path):
                return output_path
            else:
                raise Exception("Video conversion failed - output not found")
                
        except Exception as e:
            logger.error(f"Video conversion error: {e}")
            raise Exception(f"Video to {output_format} conversion failed")
    
    async def extract_audio(self, input_path: str, output_format: str = 'mp3') -> str:
        """Extract audio from video"""
        output_path = os.path.splitext(input_path)[0] + f'_audio.{output_format}'
        
        try:
            from moviepy.editor import VideoFileClip
            
            clip = VideoFileClip(input_path)
            clip.audio.write_audiofile(output_path)
            clip.close()
            return output_path
        except ImportError:
            # Fallback to FFmpeg
            cmd = [
                'ffmpeg', '-i', input_path, '-y',
                '-vn', '-acodec', 'libmp3lame' if output_format == 'mp3' else 'copy',
                output_path
            ]
            
            await self._run_command(cmd)
            return output_path
    
    async def create_gif(self, input_path: str, start_time: str = "00:00:00", duration: str = "5") -> str:
        """Create GIF from video"""
        output_path = os.path.splitext(input_path)[0] + '.gif'
        
        try:
            from moviepy.editor import VideoFileClip
            
            clip = VideoFileClip(input_path).subclip(start_time, start_time + int(duration))
            clip = clip.resize(height=240)  # Resize for smaller GIF
            clip.write_gif(output_path, fps=10)
            clip.close()
            return output_path
        except ImportError:
            # Fallback to FFmpeg
            cmd = [
                'ffmpeg', '-i', input_path, '-y',
                '-ss', start_time, '-t', duration,
                '-vf', 'fps=10,scale=320:-1:flags=lanczos',
                output_path
            ]
            
            await self._run_command(cmd)
            return output_path
    
    async def compress_video(self, input_path: str) -> str:
        """Compress video file"""
        output_path = os.path.splitext(input_path)[0] + '_compressed.mp4'
        
        cmd = [
            'ffmpeg', '-i', input_path, '-y',
            '-codec:v', 'libx264', '-crf', '28',
            '-codec:a', 'aac', '-b:a', '128k',
            output_path
        ]
        
        await self._run_command(cmd)
        return output_path
    
    async def trim_video(self, input_path: str, start_time: str, end_time: str) -> str:
        """Trim video file"""
        output_path = os.path.splitext(input_path)[0] + '_trimmed.mp4'
        
        cmd = [
            'ffmpeg', '-i', input_path, '-y',
            '-ss', start_time, '-to', end_time,
            '-codec', 'copy', output_path
        ]
        
        await self._run_command(cmd)
        return output_path
    
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
video_converter = VideoConverter()