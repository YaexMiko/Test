# core/ffmpeg.py
import asyncio
import logging
import os
import subprocess
import re
import json
from config import FFMPEG_PATH

logger = logging.getLogger(__name__)

async def encode_video(input_path, settings, status_message=None):
    """Encode video using FFmpeg with user settings and progress tracking."""
    try:
        # Generate output filename
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = f"temp/encoded_{base_name}.mp4"
        
        # Ensure temp directory exists
        os.makedirs("temp", exist_ok=True)
        
        # Get video duration first for progress tracking
        duration = await get_video_duration(input_path)
        if not duration:
            logger.warning("Could not get video duration, progress tracking disabled")
        
        # Build FFmpeg command
        cmd = build_ffmpeg_command(input_path, output_path, settings)
        
        logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
        
        # Run FFmpeg with progress tracking
        success = await run_ffmpeg_with_progress(cmd, duration, status_message)
        
        if success and os.path.exists(output_path):
            logger.info("Video encoding completed successfully")
            return output_path
        else:
            logger.error("FFmpeg encoding failed")
            return None
            
    except Exception as e:
        logger.error(f"Error encoding video: {e}")
        return None

async def run_ffmpeg_with_progress(cmd, duration, status_message=None):
    """Run FFmpeg command with real-time progress tracking."""
    try:
        # Create a temporary progress file
        progress_file = "temp/ffmpeg_progress.txt"
        
        # Modify command to output progress to file
        progress_cmd = cmd[:-1] + [
            "-progress", progress_file,
            "-nostats",
            "-loglevel", "error"
        ] + [cmd[-1]]
        
        logger.info(f"Starting FFmpeg with progress tracking...")
        
        # Start FFmpeg process
        process = await asyncio.create_subprocess_exec(
            *progress_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Start progress monitoring task
        progress_task = None
        if duration and status_message:
            progress_task = asyncio.create_task(
                monitor_progress(progress_file, duration, status_message)
            )
        
        # Wait for process to complete
        stdout, stderr = await process.communicate()
        
        # Stop progress monitoring
        if progress_task:
            progress_task.cancel()
            try:
                await progress_task
            except asyncio.CancelledError:
                pass
        
        # Clean up progress file
        try:
            if os.path.exists(progress_file):
                os.remove(progress_file)
        except:
            pass
        
        if process.returncode == 0:
            if status_message:
                await status_message.edit_text(
                    "✅ **Video Encoding Completed!**\n\n"
                    "🎬 Processing finished successfully\n"
                    "📁 Preparing final output...",
                    parse_mode='Markdown'
                )
            return True
        else:
            logger.error(f"FFmpeg error: {stderr.decode()}")
            if status_message:
                error_msg = stderr.decode()[:200] if stderr else "Unknown encoding error"
                await status_message.edit_text(
                    f"❌ **Encoding Failed**\n\n"
                    f"Error: {error_msg}\n\n"
                    f"Try different settings or file format.",
                    parse_mode='Markdown'
                )
            return False
            
    except Exception as e:
        logger.error(f"Error running FFmpeg with progress: {e}")
        if status_message:
            await status_message.edit_text(
                f"❌ **Encoding Error**\n\n"
                f"Process failed: {str(e)[:100]}\n\n"
                f"Please try again.",
                parse_mode='Markdown'
            )
        return False

async def monitor_progress(progress_file, duration, status_message):
    """Monitor FFmpeg progress from file."""
    try:
        last_update_time = 0
        duration_seconds = time_to_seconds(duration) if duration else 0
        
        while True:
            try:
                # Check if progress file exists and read it
                if os.path.exists(progress_file):
                    with open(progress_file, 'r') as f:
                        content = f.read()
                    
                    # Parse progress
                    current_time = extract_progress_time(content)
                    
                    if current_time and duration_seconds > 0:
                        current_seconds = time_to_seconds(current_time)
                        
                        # Update progress every 3 seconds
                        current_loop_time = asyncio.get_event_loop().time()
                        if current_loop_time - last_update_time >= 3:
                            await update_encoding_progress(
                                current_time, duration, current_seconds, 
                                duration_seconds, status_message
                            )
                            last_update_time = current_loop_time
                
                # Wait before next check
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"Progress monitoring error: {e}")
                await asyncio.sleep(2)
                
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Error in progress monitoring: {e}")

def extract_progress_time(content):
    """Extract current time from FFmpeg progress output."""
    try:
        # Look for out_time_ms or out_time
        lines = content.strip().split('\n')
        
        for line in lines:
            if line.startswith('out_time='):
                time_str = line.split('=')[1].strip()
                return time_str
            elif line.startswith('out_time_ms='):
                # Convert microseconds to time
                microseconds = int(line.split('=')[1])
                seconds = microseconds / 1000000
                return seconds_to_time(seconds)
        
        return None
        
    except Exception as e:
        logger.debug(f"Error extracting progress time: {e}")
        return None

async def update_encoding_progress(current_time, total_duration, current_seconds, total_seconds, status_message):
    """Update encoding progress message."""
    try:
        if not status_message:
            return
        
        progress_percent = min((current_seconds / total_seconds) * 100, 100)
        
        # Create progress bar
        progress_bar = create_progress_bar(progress_percent)
        
        # Calculate remaining time
        if progress_percent > 0 and progress_percent < 100:
            elapsed_time = current_seconds
            estimated_total = elapsed_time / (progress_percent / 100)
            remaining_time = max(0, estimated_total - elapsed_time)
            remaining_str = seconds_to_time(remaining_time)
        else:
            remaining_str = "Calculating..."
        
        # Calculate encoding speed
        fps_info = ""
        
        # Update message
        await status_message.edit_text(
            f"🔄 **Encoding Video**\n\n"
            f"{progress_bar}\n\n"
            f"📊 Progress: {progress_percent:.1f}%\n"
            f"⏱️ Time: {current_time} / {total_duration}\n"
            f"⏳ Remaining: ~{remaining_str}\n"
            f"🎬 Processing video stream...",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.debug(f"Error updating progress: {e}")

def create_progress_bar(percentage, length=15):
    """Create a visual progress bar."""
    try:
        filled = int(length * percentage / 100)
        empty = length - filled
        
        # Use Unicode characters for progress bar
        bar = "█" * filled + "░" * empty
        return f"[{bar}] {percentage:.1f}%"
    except:
        return f"Progress: {percentage:.1f}%"

def time_to_seconds(time_str):
    """Convert time string (HH:MM:SS.ms) to seconds."""
    try:
        if isinstance(time_str, (int, float)):
            return float(time_str)
        
        # Handle different time formats
        if "." in time_str:
            time_str = time_str.split(".")[0]  # Remove milliseconds
        
        parts = time_str.split(":")
        if len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        else:
            return int(parts[0])
    except:
        return 0

def seconds_to_time(seconds):
    """Convert seconds to time string (HH:MM:SS)."""
    try:
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    except:
        return "00:00:00"

async def get_video_duration(file_path):
    """Get video duration using FFprobe."""
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
            data = json.loads(stdout.decode())
            
            # Try to get duration from format first
            if 'format' in data and 'duration' in data['format']:
                duration_seconds = float(data['format']['duration'])
                return seconds_to_time(duration_seconds)
            
            # Fallback to streams
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video' and 'duration' in stream:
                    duration_seconds = float(stream['duration'])
                    return seconds_to_time(duration_seconds)
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting video duration: {e}")
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
    
    # Preset for encoding speed vs compression
    cmd.extend(["-preset", "medium"])
    
    # Overwrite output file
    cmd.append("-y")
    
    # Output file
    cmd.append(output_path)
    
    return cmd

async def get_video_info(file_path):
    """Get detailed video information using FFprobe."""
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
            return json.loads(stdout.decode())
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        return None

async def get_encoding_stats(file_path):
    """Get encoding statistics for the processed file."""
    try:
        info = await get_video_info(file_path)
        if not info:
            return None
        
        stats = {
            'duration': '00:00:00',
            'bitrate': '0',
            'size': 0,
            'codec': 'unknown',
            'resolution': 'unknown'
        }
        
        # Get format info
        if 'format' in info:
            format_info = info['format']
            if 'duration' in format_info:
                duration_seconds = float(format_info['duration'])
                stats['duration'] = seconds_to_time(duration_seconds)
            if 'bit_rate' in format_info:
                stats['bitrate'] = f"{int(format_info['bit_rate']) // 1000}k"
            if 'size' in format_info:
                stats['size'] = int(format_info['size'])
        
        # Get video stream info
        for stream in info.get('streams', []):
            if stream.get('codec_type') == 'video':
                stats['codec'] = stream.get('codec_name', 'unknown')
                width = stream.get('width', 0)
                height = stream.get('height', 0)
                if width and height:
                    stats['resolution'] = f"{width}x{height}"
                break
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting encoding stats: {e}")
        return None

# Fallback encoding function without progress
async def encode_video_simple(input_path, output_path, settings):
    """Simple encoding without progress tracking (fallback)."""
    try:
        cmd = build_ffmpeg_command(input_path, output_path, settings)
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            logger.info("Simple encoding completed successfully")
            return True
        else:
            logger.error(f"Simple encoding failed: {stderr.decode()}")
            return False
            
    except Exception as e:
        logger.error(f"Error in simple encoding: {e}")
        return False
