# core/ffmpeg.py
import asyncio
import logging
import os
import subprocess
from config import FFMPEG_PATH

logger = logging.getLogger(__name__)

async def encode_video(input_path, settings, status_message=None):
    """Encode video using FFmpeg with user settings."""
    try:
        # Generate output filename
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = f"temp/encoded_{base_name}.mp4"
        
        # Ensure temp directory exists
        os.makedirs("temp", exist_ok=True)
        
        # Build FFmpeg command
        cmd = build_ffmpeg_command(input_path, output_path, settings)
        
        logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
        
        # Run FFmpeg
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            logger.info("Video encoding completed successfully")
            return output_path
        else:
            logger.error(f"FFmpeg error: {stderr.decode()}")
            return None
            
    except Exception as e:
        logger.error(f"Error encoding video: {e}")
        return None

def build_ffmpeg_command(input_path, output_path, settings):
    """Build FFmpeg command based on user settings."""
    cmd = [FFMPEG_PATH, "-i", input_path]
    
    # Video codec
    if settings['vcodec'] == 'x264':
        cmd.extend(["-c:v", "libx264"])
    else:  # x265
        cmd.extend(["-c:v", "libx265"])
    
    # Pixel format based on bit depth
    if settings['bits'] == '10':
        cmd.extend(["-pix_fmt", "yuv420p10le"])
    else:
        cmd.extend(["-pix_fmt", "yuv420p"])
    
    # CRF (quality)
    cmd.extend(["-crf", settings['crf']])
    
    # Resolution
    resolution_map = {
        '240': '426x240',
        '360': '640x360',
        '480': '854x480',
        '576': '1024x576',
        '720': '1280x720',
        '1080': '1920x1080'
    }
    
    if settings['resolution'] in resolution_map:
        cmd.extend(["-s", resolution_map[settings['resolution']]])
    
    # Audio codec
    cmd.extend(["-c:a", "aac", "-b:a", "128k"])
    
    # Preset for faster encoding
    cmd.extend(["-preset", "medium"])
    
    # Overwrite output file
    cmd.append("-y")
    
    # Output file
    cmd.append(output_path)
    
    return cmd

async def get_video_info(file_path):
    """Get video information using FFprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", file_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            import json
            return json.loads(stdout.decode())
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        return None
