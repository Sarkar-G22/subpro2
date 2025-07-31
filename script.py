#!/usr/bin/env python3
"""
Subtitle Generator - Enhanced Version
A comprehensive tool for automatic subtitle generation and video processing.

Features:
- Multiple audio extraction methods (FFmpeg, MoviePy)
- Local Whisper transcription with word timestamps
- Robust subtitle burning with fallback mechanisms
- Cross-platform compatibility
- Progress tracking and detailed error reporting
"""

import os
import subprocess
import tempfile
import shutil
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, Callable
import sys
import time
import re
import json
from dataclasses import dataclass

# Try to import whisper
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

# Try to import moviepy
try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

# Try to import opencv
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('subtitle_generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class FontSettings:
    """Font configuration for subtitle styling"""
    family: str = 'Arial'
    size: int = 24
    color: str = 'white'
    outline_color: str = 'black'
    bold: bool = False
    italic: bool = False
    shadow: bool = True
    
    def to_ffmpeg_style(self) -> str:
        """Convert font settings to FFmpeg subtitle style string"""
        style_parts = []
        style_parts.append(f"FontName={self.family}")
        style_parts.append(f"FontSize={self.size}")
        style_parts.append(f"PrimaryColour={self._color_to_ass(self.color)}")
        style_parts.append(f"OutlineColour={self._color_to_ass(self.outline_color)}")
        if self.bold:
            style_parts.append("Bold=1")
        if self.italic:
            style_parts.append("Italic=1")
        if self.shadow:
            style_parts.append("Shadow=2")
        return ','.join(style_parts)
    
    def _color_to_ass(self, color: str) -> str:
        """Convert color name or hex to ASS format"""
        # Handle hex colors (e.g., #ffffff)
        if color.startswith('#'):
            hex_color = color[1:]
            if len(hex_color) == 6:
                # Convert RGB to BGR for ASS format
                r = hex_color[0:2]
                g = hex_color[2:4]
                b = hex_color[4:6]
                return f'&H{b}{g}{r}'
        
        # Handle named colors
        color_map = {
            'white': '&Hffffff',
            'black': '&H000000',
            'red': '&H0000ff',
            'green': '&H00ff00',
            'blue': '&Hff0000',
            'yellow': '&H00ffff',
            '#ffffff': '&Hffffff',
            '#000000': '&H000000'
        }
        return color_map.get(color.lower(), '&Hffffff')

class LocalWhisperTools:
    """Enhanced Whisper tool for local transcription with improved Hindi/Hinglish support"""
    
    SUPPORTED_MODELS = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]
    
    # Language codes and configurations for better Hindi/Hinglish support
    LANGUAGE_CONFIGS = {
        'hindi': {
            'code': 'hi',
            'name': 'Hindi',
            'script': 'devanagari',
            'romanize': False
        },
        'hinglish': {
            'code': 'hi',  # Use Hindi model but expect English mixed content
            'name': 'Hinglish',
            'script': 'latin',
            'romanize': True
        },
        'english': {
            'code': 'en',
            'name': 'English',
            'script': 'latin',
            'romanize': False
        }
    }
    
    # Hindi words that commonly appear in Hinglish
    HINDI_INDICATORS = [
        'है', 'हैं', 'था', 'थी', 'करना', 'कर', 'और', 'का', 'की', 'के', 'में', 'से', 'को', 'पर',
        'यह', 'वह', 'हम', 'तुम', 'आप', 'मैं', 'ये', 'वो', 'क्या', 'कैसे', 'कहाँ', 'कब', 'क्यों',
        'अच्छा', 'बुरा', 'बड़ा', 'छोटा', 'नया', 'पुराना', 'सही', 'गलत'
    ]
    
    def __init__(self, model_name: str = "base"):
        """Initialize Whisper model with validation and Hindi/Hinglish optimization"""
        if not WHISPER_AVAILABLE:
            raise ImportError("Whisper is not available. Install it with: pip install openai-whisper")
        
        if model_name not in self.SUPPORTED_MODELS:
            logger.warning(f"Model '{model_name}' not in supported models {self.SUPPORTED_MODELS}. Proceeding anyway.")
        
        # Recommend larger models for Hindi/Hinglish accuracy
        if model_name in ['tiny', 'base']:
            logger.warning("For better Hindi/Hinglish accuracy, consider using 'small' or larger models")
        
        try:
            logger.info(f"Loading Whisper model: {model_name}")
            self.model = whisper.load_model(model_name)
            self.model_name = model_name
            self.name = "local_whisper_tools"
            logger.info(f"Successfully loaded Whisper model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load Whisper model '{model_name}': {e}")
            raise Exception(f"Failed to load Whisper model: {e}")
    
    def detect_language_type(self, audio_path: str, progress_callback: Optional[Callable] = None) -> str:
        """Detect if audio is Hindi, Hinglish, or English using a quick sample"""
        try:
            if progress_callback:
                progress_callback("🔍 Detecting language type...")
            
            # Use a quick transcription of first 30 seconds to detect language
            quick_result = self.model.transcribe(
                audio_path,
                language=None,  # Auto-detect
                task="transcribe",
                verbose=False,
                condition_on_previous_text=False,
                word_timestamps=False,
                duration=30  # Only first 30 seconds
            )
            
            detected_lang = quick_result.get('language', 'en')
            text_sample = quick_result.get('text', '').lower()
            
            logger.info(f"Initial language detection: {detected_lang}")
            logger.info(f"Sample text: {text_sample[:100]}...")
            
            # Check for Hindi script or words
            hindi_script_count = len(re.findall(r'[\u0900-\u097F]', text_sample))
            
            # Check for Hindi words in romanized text
            hindi_word_matches = sum(1 for word in self.HINDI_INDICATORS 
                                   if any(variant in text_sample for variant in [
                                       word, self._romanize_hindi_word(word)
                                   ]))
            
            # Decision logic
            if detected_lang == 'hi' or hindi_script_count > 10:
                if hindi_script_count > len(text_sample) * 0.3:  # More than 30% Hindi script
                    language_type = 'hindi'
                else:
                    language_type = 'hinglish'  # Mix of Hindi and English
            elif hindi_word_matches > 3 or any(word in text_sample for word in 
                                             ['hai', 'kar', 'kya', 'kaise', 'acha', 'bura']):
                language_type = 'hinglish'
            else:
                language_type = 'english'
            
            logger.info(f"Detected language type: {language_type}")
            
            if progress_callback:
                progress_callback(f"🌐 Detected language: {self.LANGUAGE_CONFIGS[language_type]['name']}")
            
            return language_type
            
        except Exception as e:
            logger.warning(f"Language detection failed: {e}. Defaulting to hinglish.")
            return 'hinglish'
    
    def _romanize_hindi_word(self, hindi_word: str) -> str:
        """Simple romanization mapping for common Hindi words"""
        romanization_map = {
            'है': 'hai', 'हैं': 'hain', 'था': 'tha', 'थी': 'thi',
            'करना': 'karna', 'कर': 'kar', 'और': 'aur',
            'का': 'ka', 'की': 'ki', 'के': 'ke', 'में': 'mein',
            'से': 'se', 'को': 'ko', 'पर': 'par',
            'यह': 'yah', 'वह': 'vah', 'हम': 'hum',
            'तुम': 'tum', 'आप': 'aap', 'मैं': 'main',
            'क्या': 'kya', 'कैसे': 'kaise', 'कहाँ': 'kahan',
            'अच्छा': 'acha', 'बुरा': 'bura'
        }
        return romanization_map.get(hindi_word, hindi_word)
    
    def transcribe_audio_local(self, audio_path: str, progress_callback: Optional[Callable] = None, 
                              language: Optional[str] = None, task: str = "transcribe",
                              auto_detect_language: bool = True) -> str:
        """Transcribe audio file with enhanced Hindi/Hinglish support"""
        try:
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            if progress_callback:
                progress_callback(f"🎤 Starting transcription with {self.model_name} model...")
            
            # Auto-detect language if not specified and auto_detect is enabled
            if auto_detect_language and not language:
                detected_type = self.detect_language_type(audio_path, progress_callback)
                language_config = self.LANGUAGE_CONFIGS[detected_type]
                language = language_config['code']
                logger.info(f"Using detected language: {language} for {detected_type}")
            elif language:
                # Map common language inputs
                language_mapping = {
                    'hindi': 'hi',
                    'hinglish': 'hi',  # Use Hindi model for Hinglish
                    'english': 'en'
                }
                language = language_mapping.get(language.lower(), language)
            
            # Prepare enhanced transcription options for Hindi/Hinglish
            transcribe_options = {
                "word_timestamps": True,
                "task": task,
                "verbose": False,
                "condition_on_previous_text": True,  # Better context for mixed languages
                "temperature": 0.0,  # More deterministic for better accuracy
                "compression_ratio_threshold": 2.4,  # Detect repetitive transcriptions
                "logprob_threshold": -1.0,  # Filter low-confidence segments
                "no_speech_threshold": 0.6  # Better silence detection
            }
            
            if language:
                transcribe_options["language"] = language
                logger.info(f"Transcribing in language: {language}")
            
            logger.info(f"Starting transcription of: {audio_path}")
            start_time = time.time()
            
            # Multiple pass transcription for better accuracy
            if progress_callback:
                progress_callback("🎤 Running primary transcription pass...")
            
            result = self.model.transcribe(audio_path, **transcribe_options)
            
            # If confidence is low, try with different parameters
            avg_logprob = sum(segment.get('avg_logprob', -1.0) for segment in result.get('segments', [])) / max(len(result.get('segments', [])), 1)
            
            if avg_logprob < -0.8 and language == 'hi':  # Low confidence for Hindi
                if progress_callback:
                    progress_callback("🔄 Low confidence detected, trying alternative approach...")
                
                # Try without language specification for mixed content
                transcribe_options_alt = transcribe_options.copy()
                transcribe_options_alt.pop('language', None)
                transcribe_options_alt['temperature'] = 0.2  # Slightly more creative
                
                result_alt = self.model.transcribe(audio_path, **transcribe_options_alt)
                
                # Use alternative result if it has better confidence
                avg_logprob_alt = sum(segment.get('avg_logprob', -1.0) for segment in result_alt.get('segments', [])) / max(len(result_alt.get('segments', [])), 1)
                
                if avg_logprob_alt > avg_logprob:
                    result = result_alt
                    logger.info("Using alternative transcription with better confidence")
            
            end_time = time.time()
            duration = end_time - start_time
            
            if progress_callback:
                progress_callback(f"🎤 Transcription completed in {duration:.1f}s. Processing segments...")
            
            logger.info(f"Transcription completed in {duration:.1f} seconds")
            
            # Validate result
            if not result or 'segments' not in result:
                raise ValueError("Invalid transcription result - no segments found")
            
            # Post-process for Hindi/Hinglish specific improvements
            processed_result = self._post_process_hindi_hinglish(result, language)
            
            srt_content = self._convert_to_srt(processed_result)
            
            if not srt_content.strip():
                raise ValueError("Generated SRT content is empty")
            
            logger.info(f"Generated SRT with {len(processed_result['segments'])} segments")
            return srt_content
        
        except Exception as e:
            error_msg = f"Error transcribing audio: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def _post_process_hindi_hinglish(self, result: Dict[str, Any], language: Optional[str] = None) -> Dict[str, Any]:
        """Post-process transcription result for Hindi/Hinglish specific improvements"""
        if 'segments' not in result:
            return result
        
        processed_segments = []
        
        for segment in result['segments']:
            text = segment.get('text', '').strip()
            
            if not text:
                continue
            
            # Fix common Hindi/Hinglish transcription errors
            text = self._fix_hindi_hinglish_errors(text)
            
            # Filter out segments with very low confidence for Hindi
            if language == 'hi' and segment.get('avg_logprob', 0) < -1.5:
                logger.debug(f"Skipping low confidence segment: {text[:50]}...")
                continue
            
            # Update segment with processed text
            processed_segment = segment.copy()
            processed_segment['text'] = text
            processed_segments.append(processed_segment)
        
        result['segments'] = processed_segments
        return result
    
    def _fix_hindi_hinglish_errors(self, text: str) -> str:
        """Fix common transcription errors in Hindi/Hinglish text"""
        # Common corrections for Hindi/Hinglish
        corrections = {
            # English words commonly mistranscribed
            'और': 'aur',  # Keep 'and' in romanized form for Hinglish
            'है ना': 'hai na',
            'क्या': 'kya',
            'कैसे': 'kaise',
            'अच्छा': 'accha',
            'बहुत': 'bahut',
            'थोड़ा': 'thoda',
            
            # Common misheard words
            'theek': 'thik',
            'paani': 'pani',
            'ghar': 'ghar',
            'kaun': 'kaun',
            'kyun': 'kyun',
            
            # Fix spacing issues
            'hai na': 'hai na',
            'kar na': 'karna',
            'ja na': 'jana',
            'aa na': 'aana',
        }
        
        # Apply corrections
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
        
        # Clean up extra spaces and punctuation
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'([.!?])\s*([.!?])+', r'\1', text)  # Remove repeated punctuation
        
        # Ensure proper capitalization for mixed content
        sentences = re.split(r'([.!?]\s*)', text)
        processed_sentences = []
        
        for sentence in sentences:
            if sentence.strip() and not re.match(r'[.!?]\s*', sentence):
                # Capitalize first letter of each sentence
                sentence = sentence.strip()
                if sentence:
                    sentence = sentence[0].upper() + sentence[1:]
            processed_sentences.append(sentence)
        
        return ''.join(processed_sentences).strip()
    
    def _convert_to_srt(self, result: Dict[str, Any]) -> str:
        """Convert Whisper result to SRT format with improved Hindi/Hinglish text processing"""
        srt_lines = []
        
        if 'segments' not in result:
            logger.warning("No segments found in transcription result")
            return ""
        
        segment_counter = 1
        
        for segment in result['segments']:
            start_time = self._format_timestamp(segment.get('start', 0))
            end_time = self._format_timestamp(segment.get('end', 0))
            text = segment.get('text', '').strip()
            
            # Skip empty segments
            if not text:
                continue
            
            # Additional cleaning for Hindi/Hinglish
            text = self._clean_subtitle_text(text)
            
            # Skip very short segments (likely noise) but be more lenient for Hindi
            if len(text) < 1 or (len(text) < 3 and not re.search(r'[\u0900-\u097F]', text)):
                continue
            
            # Skip segments that are just punctuation or numbers
            if re.match(r'^[\s\d\W]+$', text) and not re.search(r'[\u0900-\u097F\w]', text):
                continue
            
            srt_lines.append(str(segment_counter))
            srt_lines.append(f"{start_time} --> {end_time}")
            srt_lines.append(text)
            srt_lines.append("")
            
            segment_counter += 1
        
        return "\n".join(srt_lines)
    
    def _clean_subtitle_text(self, text: str) -> str:
        """Clean subtitle text for better readability in Hindi/Hinglish"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common formatting issues
        text = re.sub(r'\s*([,.!?])\s*', r'\1 ', text)  # Fix punctuation spacing
        text = re.sub(r'\s+([,.!?])', r'\1', text)  # Remove space before punctuation
        
        # Remove leading/trailing whitespace and punctuation artifacts
        text = text.strip(' .,!?')
        
        # Ensure text doesn't start with lowercase after punctuation
        text = re.sub(r'([.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)
        
        return text
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format timestamp for SRT format with validation"""
        if not isinstance(seconds, (int, float)) or seconds < 0:
            logger.warning(f"Invalid timestamp: {seconds}, using 0")
            seconds = 0
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

class VideoProcessor:
    """Enhanced video processing class with robust subtitle burning and improved error handling"""
    
    def __init__(self):
        self.moviepy_available = MOVIEPY_AVAILABLE
        self.opencv_available = OPENCV_AVAILABLE
        self.ffmpeg_available = self._check_ffmpeg()
        
        # Log available tools
        logger.info(f"VideoProcessor initialized - FFmpeg: {self.ffmpeg_available}, "
                   f"MoviePy: {self.moviepy_available}, OpenCV: {self.opencv_available}")
    
    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available and get version info"""
        try:
            result = subprocess.run(['ffmpeg', '-version'],
                                  capture_output=True, check=True, text=True, timeout=10)
            
            # Extract version info
            version_line = result.stdout.split('\n')[0]
            logger.info(f"FFmpeg detected: {version_line}")
            return True
        except subprocess.TimeoutExpired:
            logger.warning("FFmpeg version check timed out")
            return False
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning(f"FFmpeg not available: {e}")
            return False
    
    def extract_audio(self, video_path: str, audio_path: str, progress_callback=None) -> bool:
        """Extract audio from video using available methods"""
        
        # Method 1: FFmpeg (most reliable)
        if self.ffmpeg_available:
            try:
                if progress_callback:
                    progress_callback("🎵 Extracting audio with FFmpeg...")
                
                cmd = [
                    'ffmpeg', '-i', video_path,
                    '-vn',  # No video
                    '-acodec', 'pcm_s16le',
                    '-ar', '16000',  # 16kHz sample rate
                    '-ac', '1',      # Mono
                    '-y',            # Overwrite output
                    audio_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    return True
                else:
                    if progress_callback:
                        progress_callback(f"⚠️ FFmpeg failed: {result.stderr}")
            except Exception as e:
                if progress_callback:
                    progress_callback(f"⚠️ FFmpeg error: {e}")
        
        # Method 2: MoviePy (fallback)
        if self.moviepy_available:
            try:
                if progress_callback:
                    progress_callback("🎵 Extracting audio with MoviePy...")
                
                video_clip = VideoFileClip(video_path)
                video_clip.audio.write_audiofile(
                    audio_path,
                    verbose=False,
                    logger=None,
                    temp_audiofile=None,
                    remove_temp=True
                )
                video_clip.close()
                return True
            except Exception as e:
                if progress_callback:
                    progress_callback(f"⚠️ MoviePy failed: {e}")
        
        return False

    def validate_srt_file(self, srt_path: str) -> Tuple[bool, str]:
        """Validate SRT file format and content"""
        try:
            if not os.path.exists(srt_path):
                return False, "SRT file does not exist"
            
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                return False, "SRT file is empty"
            
            # Basic SRT validation - check for sequence numbers and timestamps
            lines = content.split('\n')
            if len(lines) < 3:
                return False, "SRT file too short"
            
            # Check if first line is a number
            if not lines[0].strip().isdigit():
                return False, "SRT file doesn't start with sequence number"
            
            # Check for timestamp format
            timestamp_found = False
            for line in lines[:10]:  # Check first 10 lines
                if '-->' in line:
                    timestamp_found = True
                    break
            
            if not timestamp_found:
                return False, "No timestamp found in SRT file"
            
            return True, "SRT file is valid"
            
        except Exception as e:
            return False, f"Error validating SRT file: {e}"

    def normalize_path(self, path: str) -> str:
        """Normalize path for FFmpeg (especially for Windows)"""
        # Convert to forward slashes and escape special characters
        normalized = path.replace('\\', '/')
        # Escape special characters for FFmpeg
        normalized = normalized.replace(':', '\\:')
        return normalized

    def create_styled_ass_file(self, srt_path: str, ass_path: str, font_settings: FontSettings) -> bool:
        """Create ASS file with custom styling from SRT file"""
        try:
            # Read SRT content
            with open(srt_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()
            
            # Parse SRT to extract subtitle data
            subtitles = []
            blocks = srt_content.strip().split('\n\n')
            
            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) >= 3:
                    try:
                        id_num = int(lines[0])
                        time_match = re.match(r'(\d{2}:\d{2}:\d{2}),(\d{3}) --> (\d{2}:\d{2}:\d{2}),(\d{3})', lines[1])
                        if time_match:
                            start_time = f"{time_match.group(1)}.{time_match.group(2)[:2]}"
                            end_time = f"{time_match.group(3)}.{time_match.group(4)[:2]}"
                            text = '\n'.join(lines[2:])
                            subtitles.append((start_time, end_time, text))
                    except (ValueError, AttributeError):
                        continue
            
            # Create ASS content with advanced styling
            ass_content = f"""[Script Info]
Title: Generated Subtitles
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_settings.family},{font_settings.size},{font_settings._color_to_ass(font_settings.color)},&H000000ff,{font_settings._color_to_ass(font_settings.outline_color)},&H80000000,{1 if font_settings.bold else 0},{1 if font_settings.italic else 0},0,0,100,100,0,0,1,2,{2 if font_settings.shadow else 0},2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
            
            # Add subtitle events
            for start_time, end_time, text in subtitles:
                # Clean text for ASS format
                text = text.replace('\n', '\\N')
                ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}\n"
            
            # Write ASS file
            with open(ass_path, 'w', encoding='utf-8') as f:
                f.write(ass_content)
            
            logger.info(f"Created ASS file with styling: {ass_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating ASS file: {e}")
            return False

    def burn_subtitles_to_video(self, video_path: str, srt_path: str, output_path: str, font_settings=None, progress_callback=None) -> bool:
        """Fixed subtitle burning with proper error handling"""
        
        if not self.ffmpeg_available:
            if progress_callback:
                progress_callback("❌ FFmpeg not available for subtitle burning")
            return False
        
        # Validate SRT file first
        is_valid, validation_message = self.validate_srt_file(srt_path)
        if not is_valid:
            if progress_callback:
                progress_callback(f"❌ Invalid SRT file: {validation_message}")
            return False
        
        try:
            if progress_callback:
                progress_callback("🔥 Burning subtitles into video...")
            
            # Method 1: Use ASS file with custom styling (best for styling)
            try:
                if progress_callback:
                    progress_callback("🔥 Creating styled ASS file for better subtitle appearance...")
                
                # Create ASS file with font settings
                ass_path = srt_path.replace('.srt', '.ass')
                if self.create_styled_ass_file(srt_path, ass_path, font_settings or FontSettings()):
                    if progress_callback:
                        progress_callback("🔥 Burning subtitles with advanced styling...")
                    
                    # Normalize path for cross-platform compatibility
                    normalized_ass = self.normalize_path(ass_path)
                    
                    cmd = [
                        'ffmpeg', '-i', video_path,
                        '-vf', f'ass={normalized_ass}',
                        '-c:a', 'copy',  # Copy audio without re-encoding
                        '-c:v', 'libx264',  # Ensure proper video codec
                        '-preset', 'fast',  # Faster encoding
                        '-y',  # Overwrite output file
                        output_path
                    ]
                    
                    if progress_callback:
                        progress_callback(f"🎬 Running styled subtitle command...")
                    
                    # Run FFmpeg with timeout
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=600  # 10 minute timeout
                    )
                    
                    if result.returncode == 0:
                        if progress_callback:
                            progress_callback("✅ Subtitles burned successfully with advanced styling!")
                        # Clean up ASS file
                        try:
                            os.remove(ass_path)
                        except:
                            pass
                        return True
                    else:
                        if progress_callback:
                            progress_callback(f"⚠️ ASS styling method failed: {result.stderr[:200]}")
                
            except subprocess.TimeoutExpired:
                if progress_callback:
                    progress_callback("⚠️ ASS method timed out, trying fallback...")
            except Exception as e:
                if progress_callback:
                    progress_callback(f"⚠️ ASS method error: {e}")
            
            # Method 2: Simple subtitle filter (fallback)
            try:
                if progress_callback:
                    progress_callback("🔥 Attempting simple subtitle burning...")
                
                # Normalize path for cross-platform compatibility
                normalized_srt = self.normalize_path(srt_path)
                
                cmd = [
                    'ffmpeg', '-i', video_path,
                    '-vf', f'subtitles={normalized_srt}',
                    '-c:a', 'copy',  # Copy audio without re-encoding
                    '-c:v', 'libx264',  # Ensure proper video codec
                    '-preset', 'fast',  # Faster encoding
                    '-y',  # Overwrite output file
                    output_path
                ]
                
                if progress_callback:
                    progress_callback(f"🎬 Running command: {' '.join(cmd[:5])}...")
                
                # Run FFmpeg with timeout
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minute timeout
                )
                
                if result.returncode == 0:
                    if progress_callback:
                        progress_callback("✅ Subtitles burned successfully with simple method!")
                    return True
                else:
                    if progress_callback:
                        progress_callback(f"⚠️ Simple method failed: {result.stderr[:200]}")
                
            except subprocess.TimeoutExpired:
                if progress_callback:
                    progress_callback("⚠️ Simple method timed out, trying alternative...")
            except Exception as e:
                if progress_callback:
                    progress_callback(f"⚠️ Simple method error: {e}")
            
            # Method 2: Copy SRT to same directory (for path issues)
            try:
                if progress_callback:
                    progress_callback("🔥 Trying with copied SRT file...")
                
                # Copy SRT to same directory as video
                video_dir = os.path.dirname(video_path)
                temp_srt = os.path.join(video_dir, "temp_subtitles.srt")
                
                shutil.copy2(srt_path, temp_srt)
                
                cmd = [
                    'ffmpeg', '-i', video_path,
                    '-vf', f'subtitles=temp_subtitles.srt',
                    '-c:a', 'copy',
                    '-c:v', 'libx264',
                    '-preset', 'fast',
                    '-y',
                    output_path
                ]
                
                # Change working directory to video directory
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=video_dir,
                    timeout=600
                )
                
                # Clean up temp file
                if os.path.exists(temp_srt):
                    os.remove(temp_srt)
                
                if result.returncode == 0:
                    if progress_callback:
                        progress_callback("✅ Subtitles burned successfully with copied SRT method!")
                    return True
                else:
                    if progress_callback:
                        progress_callback(f"⚠️ Copied SRT method failed: {result.stderr[:200]}")
                        
            except Exception as e:
                if progress_callback:
                    progress_callback(f"⚠️ Copied SRT method error: {e}")
            
            # Method 3: Using ass filter (last resort)
            try:
                if progress_callback:
                    progress_callback("🔥 Trying ASS subtitle filter...")
                
                cmd = [
                    'ffmpeg', '-i', video_path,
                    '-vf', f'ass={srt_path}',
                    '-c:a', 'copy',
                    '-c:v', 'libx264',
                    '-preset', 'fast',
                    '-y',
                    output_path
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                
                if result.returncode == 0:
                    if progress_callback:
                        progress_callback("✅ Subtitles burned successfully with ASS filter!")
                    return True
                else:
                    if progress_callback:
                        progress_callback(f"⚠️ ASS filter failed: {result.stderr[:200]}")
                        
            except Exception as e:
                if progress_callback:
                    progress_callback(f"⚠️ ASS filter error: {e}")
            
            # If all methods failed
            if progress_callback:
                progress_callback("❌ All subtitle burning methods failed")
            return False
                
        except Exception as e:
            if progress_callback:
                progress_callback(f"❌ Unexpected error in subtitle burning: {e}")
            return False

    def create_video_with_subtitles(self, video_path: str, srt_path: str, output_dir: str, font_settings=None, progress_callback=None) -> Tuple[Optional[str], str]:
        """Create video with burned-in subtitles"""
        
        try:
            # Create unique output filename
            video_name = Path(video_path).stem
            output_filename = f"{video_name}_with_subtitles_{int(time.time())}.mp4"
            output_path = Path(output_dir) / output_filename
            
            if progress_callback:
                progress_callback(f"📹 Output will be saved as: {output_filename}")
            
            success = self.burn_subtitles_to_video(
                video_path, srt_path, str(output_path), font_settings, progress_callback
            )
            
            if success and output_path.exists():
                file_size = output_path.stat().st_size / (1024*1024)  # Size in MB
                if progress_callback:
                    progress_callback(f"✅ Video created successfully! Size: {file_size:.1f}MB")
                return str(output_path), "Video with subtitles created successfully"
            else:
                return None, "Failed to create video with subtitles - check FFmpeg installation and file permissions"
                
        except Exception as e:
            return None, f"Error creating video with subtitles: {e}"

def check_dependencies() -> Dict[str, bool]:
    """Check available dependencies with detailed logging"""
    deps = {
        'whisper': WHISPER_AVAILABLE,
        'moviepy': MOVIEPY_AVAILABLE,
        'opencv': OPENCV_AVAILABLE,
        'ffmpeg': VideoProcessor()._check_ffmpeg()
    }
    
    logger.info("Dependency check results:")
    for dep, available in deps.items():
        status = "Available" if available else "Missing"
        logger.info(f"  {dep}: {status}")
    
    # Check for critical dependencies
    if not deps['whisper']:
        logger.error("Critical dependency missing: Whisper. Install with: pip install openai-whisper")
    
    if not deps['ffmpeg'] and not deps['moviepy']:
        logger.warning("No audio extraction method available. Install FFmpeg or MoviePy.")
    
    return deps

def process_video_with_captions(video_path: str, output_dir: str, model_name: str = "base", 
                               font_settings: Optional[FontSettings] = None, create_video: bool = True, 
                               progress_callback: Optional[Callable] = None, language: Optional[str] = None,
                               auto_detect_language: bool = True):
    """Complete video captioning workflow with enhanced error handling"""
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    try:
        # Validate input file
        if not os.path.exists(video_path):
            error_msg = f"Video file not found: {video_path}"
            logger.error(error_msg)
            return None, None, error_msg
        
        # Get file info
        file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
        logger.info(f"Processing video: {video_path} ({file_size:.1f}MB)")
        
        # Initialize tools
        whisper_tools = LocalWhisperTools(model_name=model_name)
        video_processor = VideoProcessor()
        
        # Set default font settings
        if font_settings is None:
            font_settings = FontSettings()
        
        if progress_callback:
            progress_callback("🎬 Starting video captioning process...")
            progress_callback(f"📁 Output directory: {output_path}")
        
        # Step 1: Extract audio
        audio_path = output_path / "extracted_audio.wav"
        
        if progress_callback:
            progress_callback("🎵 Step 1: Extracting audio from video...")
        
        if not video_processor.extract_audio(video_path, str(audio_path), progress_callback):
            return None, None, "Failed to extract audio from video"
        
        # Step 2: Transcribe
        if progress_callback:
            progress_callback("🎤 Step 2: Transcribing audio to text...")
        
        srt_content = whisper_tools.transcribe_audio_local(
            str(audio_path), progress_callback, language, auto_detect_language=auto_detect_language
        )
        
        if srt_content.startswith("Error"):
            return None, None, srt_content
        
        # Save SRT file
        srt_path = output_path / "captions.srt"
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        if progress_callback:
            progress_callback(f"📝 Step 2 Complete: SRT file saved ({len(srt_content)} characters)")
        
        # Step 3: Create video with subtitles (optional)
        video_with_subs_path = None
        if create_video:
            if progress_callback:
                progress_callback("🎬 Step 3: Creating video with embedded subtitles...")
            
            video_with_subs_path, video_message = video_processor.create_video_with_subtitles(
                video_path, str(srt_path), str(output_path), font_settings, progress_callback
            )
            
            if not video_with_subs_path:
                if progress_callback:
                    progress_callback(f"⚠️ Video creation failed: {video_message}")
                    progress_callback("📝 But SRT file was created successfully!")
        
        if progress_callback:
            progress_callback("🎉 Video captioning process completed!")
        
        return str(srt_path), video_with_subs_path, "Success"
    
    except Exception as e:
        if progress_callback:
            progress_callback(f"❌ Unexpected error: {str(e)}")
        return None, None, f"Error during processing: {str(e)}"

def main():
    """Main function for API bridge with enhanced Hindi/Hinglish support"""
    if len(sys.argv) < 4:
        print(json.dumps({"type": "error", "message": "Usage: python script.py <video_path> <output_dir> <model_name> [create_video] [language]"}))
        sys.exit(1)
    
    video_path = sys.argv[1]
    output_dir = sys.argv[2]
    model_name = sys.argv[3]
    create_video = len(sys.argv) > 4 and sys.argv[4].lower() == 'true'
    language = sys.argv[5] if len(sys.argv) > 5 else None
    
    # Recommend better models for Hindi/Hinglish
    if language and language.lower() in ['hindi', 'hinglish', 'hi'] and model_name in ['tiny', 'base']:
        progress_callback = lambda msg: print(json.dumps({"type": "progress", "message": msg}))
        progress_callback("⚠️ For better Hindi/Hinglish accuracy, consider using 'small' or larger Whisper models")
    
    # Validate input file
    if not os.path.exists(video_path):
        print(json.dumps({"type": "error", "message": f"Video file not found: {video_path}"}))
        sys.exit(1)
    
    # Enhanced font settings
    font_settings = FontSettings(
        family='Arial',
        size=24,
        color='white',
        outline_color='black',
        bold=False,
        shadow=True
    )
    
    def progress_callback(message):
        """Send progress updates to the frontend"""
        print(json.dumps({"type": "progress", "message": message}))
        sys.stdout.flush()
    
    try:
        # Check dependencies first
        deps = check_dependencies()
        progress_callback(f"🔍 Dependencies check: {deps}")
        
        # Process video with captions
        srt_path, video_path_with_subs, message = process_video_with_captions(
            video_path,
            output_dir,
            model_name,
            font_settings,
            create_video,
            progress_callback,
            language,
            auto_detect_language=True
        )
        
        if srt_path:
            # Read the generated SRT file
            with open(srt_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()
            
            result = {
                "type": "complete",
                "srtContent": srt_content,
                "srtPath": srt_path,
                "outputDir": output_dir,
                "message": message
            }
            
            # Add video path if created
            if video_path_with_subs:
                result["videoWithSubtitles"] = video_path_with_subs
                result["videoCreated"] = True
            else:
                result["videoCreated"] = False
                result["videoError"] = "Video creation failed, but SRT file was generated successfully"
            
            print(json.dumps(result))
        else:
            print(json.dumps({
                "type": "error",
                "message": message or "Unknown error occurred"
            }))
    
    except Exception as e:
        print(json.dumps({
            "type": "error",
            "message": f"Processing failed: {str(e)}"
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()                       

     