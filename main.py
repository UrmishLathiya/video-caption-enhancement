"""
Multimodal Video Caption Enhancement System - FastAPI Backend
Author: AI Assistant
Date: August 28, 2025
"""

import os
import io
import cv2
import numpy as np
import whisper
import clip
import torch
import json
import tempfile
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from moviepy import VideoFileClip
from PIL import Image
import openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Video Caption Enhancement API",
    description="Multimodal video processing with ASR, vision analysis, and caption enhancement",
    version="1.0.0"
)

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instances (cached for performance)
whisper_model = None
clip_model = None
clip_preprocess = None
device = None

# OpenAI API key (set via environment variable)
openai.api_key = os.getenv("OPENAI_API_KEY")

def initialize_models():
    """Initialize and cache models for better performance"""
    global whisper_model, clip_model, clip_preprocess, device
    
    try:
        # Set device
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device}")
        
        # Load Whisper model
        logger.info("Loading Whisper model...")
        whisper_model = whisper.load_model("base")
        
        # Load CLIP model
        logger.info("Loading CLIP model...")
        clip_model, clip_preprocess = clip.load("ViT-B/32", device=device)
        
        logger.info("All models loaded successfully!")
        
    except Exception as e:
        logger.error(f"Error loading models: {str(e)}")
        raise

@app.on_event("startup")
async def startup_event():
    """Initialize models on startup"""
    initialize_models()

class VideoProcessor:
    """Main class for processing videos"""
    
    def __init__(self):
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.max_duration = 120  # 2 minutes
        self.num_frames = 5
    
    async def process_video(self, file: UploadFile) -> Dict[str, Any]:
        """Main processing pipeline"""
        start_time = datetime.now()
        
        try:
            # Validate file
            await self._validate_file(file)
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_path = temp_file.name
            
            try:
                # Load video
                video_clip = VideoFileClip(temp_path)
                
                # Get video info
                video_info = {
                    "duration": video_clip.duration,
                    "format": "mp4",
                    "fps": video_clip.fps,
                    "size": [video_clip.w, video_clip.h]
                }
                
                # Validate duration
                if video_info["duration"] > self.max_duration:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Video too long. Max duration: {self.max_duration}s"
                    )
                
                # Extract audio and transcribe
                transcript_result = await self._extract_and_transcribe(video_clip)
                
                # Extract and analyze frames
                visual_analysis = await self._extract_and_analyze_frames(video_clip)
                
                # Generate enhanced captions
                enhanced_captions = await self._generate_enhanced_captions(
                    transcript_result, visual_analysis
                )
                
                # Calculate processing time
                processing_time = (datetime.now() - start_time).total_seconds()
                
                result = {
                    "video_info": video_info,
                    "transcript": transcript_result,
                    "visual_analysis": visual_analysis,
                    "enhanced_captions": enhanced_captions,
                    "processing_time": processing_time,
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info(f"Video processed successfully in {processing_time:.2f}s")
                return result
                
            finally:
                # Cleanup
                video_clip.close()
                os.unlink(temp_path)
                
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _validate_file(self, file: UploadFile):
        """Validate uploaded file"""
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset
        
        if file_size > self.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {self.max_file_size / (1024*1024):.0f}MB"
            )
        
        # Check file extension
        if not file.filename.lower().endswith(('.mp4', '.mov', '.avi')):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Please upload MP4, MOV, or AVI files."
            )
    
    async def _extract_and_transcribe(self, video_clip) -> Dict[str, Any]:
        """Extract audio and perform speech recognition"""
        try:
            # Extract audio
            logger.info("Extracting audio...")
            audio = video_clip.audio
            
            if audio is None:
                return {
                    "text": "",
                    "confidence": 0.0,
                    "segments": [],
                    "language": "unknown"
                }
            
            # Save audio temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                audio.write_audiofile(temp_audio.name, verbose=False, logger=None)
                audio_path = temp_audio.name
            
            try:
                # Transcribe with Whisper
                logger.info("Transcribing audio...")
                result = whisper_model.transcribe(audio_path)
                
                # Extract segments with confidence scores
                segments = []
                for segment in result.get("segments", []):
                    segments.append({
                        "start": segment["start"],
                        "end": segment["end"],
                        "text": segment["text"].strip(),
                        "confidence": getattr(segment, 'avg_logprob', 0.0)
                    })
                
                return {
                    "text": result["text"].strip(),
                    "confidence": np.mean([s["confidence"] for s in segments]) if segments else 0.0,
                    "segments": segments,
                    "language": result.get("language", "unknown")
                }
                
            finally:
                os.unlink(audio_path)
                
        except Exception as e:
            logger.error(f"Error in audio transcription: {str(e)}")
            return {
                "text": "",
                "confidence": 0.0,
                "segments": [],
                "language": "unknown",
                "error": str(e)
            }
    
    async def _extract_and_analyze_frames(self, video_clip) -> Dict[str, Any]:
        """Extract key frames and analyze with CLIP"""
        try:
            logger.info("Extracting and analyzing frames...")
            
            duration = video_clip.duration
            frame_times = np.linspace(0, duration * 0.9, self.num_frames)  # Avoid last 10%
            
            frames = []
            frame_analyses = []
            
            for i, t in enumerate(frame_times):
                try:
                    # Extract frame
                    frame = video_clip.get_frame(t)
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    frames.append(frame_rgb)
                    
                    # Analyze frame with CLIP
                    analysis = await self._analyze_frame_with_clip(frame)
                    frame_analyses.append(analysis)
                    
                except Exception as e:
                    logger.warning(f"Error processing frame {i}: {str(e)}")
                    continue
            
            # Aggregate results
            scene_types = [analysis.get("scene_type", "unknown") for analysis in frame_analyses]
            all_objects = []
            for analysis in frame_analyses:
                all_objects.extend(analysis.get("objects", []))
            
            # Most common scene type
            scene_type = max(set(scene_types), key=scene_types.count) if scene_types else "unknown"
            
            # Unique objects
            unique_objects = list(set(all_objects))
            
            # Generate overall description
            descriptions = [analysis.get("description", "") for analysis in frame_analyses]
            overall_description = self._generate_scene_description(scene_type, unique_objects, descriptions)
            
            return {
                "scene_type": scene_type,
                "objects": unique_objects[:10],  # Top 10 objects
                "description": overall_description,
                "frame_count": len(frames),
                "individual_frames": frame_analyses
            }
            
        except Exception as e:
            logger.error(f"Error in visual analysis: {str(e)}")
            return {
                "scene_type": "unknown",
                "objects": [],
                "description": "Could not analyze video frames",
                "error": str(e)
            }
    
    async def _analyze_frame_with_clip(self, frame) -> Dict[str, Any]:
        """Analyze single frame with CLIP model"""
        try:
            # Convert to PIL Image
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            
            # Preprocess image
            image_input = clip_preprocess(image).unsqueeze(0).to(device)
            
            # Define scene types and objects to classify
            scene_types = [
                "indoor office", "outdoor scene", "presentation room", "meeting room",
                "home interior", "street scene", "nature scene", "classroom",
                "conference room", "living room"
            ]
            
            common_objects = [
                "person", "people", "computer", "laptop", "phone", "table", "chair",
                "screen", "monitor", "whiteboard", "car", "building", "tree",
                "book", "document", "microphone", "camera"
            ]
            
            # Encode text descriptions
            scene_text = clip.tokenize([f"a photo of {scene}" for scene in scene_types]).to(device)
            object_text = clip.tokenize([f"a photo of a {obj}" for obj in common_objects]).to(device)
            
            # Get predictions
            with torch.no_grad():
                # Scene classification
                scene_logits = clip_model(image_input, scene_text)[0]
                scene_probs = scene_logits.softmax(dim=-1).cpu().numpy()[0]
                
                # Object detection
                object_logits = clip_model(image_input, object_text)[0]
                object_probs = object_logits.softmax(dim=-1).cpu().numpy()[0]
            
            # Get top predictions
            scene_idx = np.argmax(scene_probs)
            scene_type = scene_types[scene_idx].replace(" ", "_")
            
            # Get objects above threshold
            threshold = 0.1
            detected_objects = [
                common_objects[i] for i, prob in enumerate(object_probs) 
                if prob > threshold
            ]
            
            # Generate description
            description = f"Scene shows {scene_type.replace('_', ' ')} with {', '.join(detected_objects[:3])}"
            
            return {
                "scene_type": scene_type,
                "scene_confidence": float(scene_probs[scene_idx]),
                "objects": detected_objects,
                "description": description
            }
            
        except Exception as e:
            logger.error(f"Error analyzing frame: {str(e)}")
            return {
                "scene_type": "unknown",
                "objects": [],
                "description": "Could not analyze frame"
            }
    
    def _generate_scene_description(self, scene_type: str, objects: List[str], descriptions: List[str]) -> str:
        """Generate overall scene description"""
        try:
            scene_readable = scene_type.replace("_", " ")
            objects_str = ", ".join(objects[:5]) if objects else "various items"
            
            return f"The video takes place in a {scene_readable} setting featuring {objects_str}. " \
                   f"The scene contains multiple elements that suggest {scene_readable} environment."
        except:
            return "Video contains various scenes and objects."
    
    async def _generate_enhanced_captions(self, transcript: Dict, visual_analysis: Dict) -> Dict[str, str]:
        """Generate enhanced captions using OpenAI GPT"""
        try:
            if not openai.api_key:
                logger.warning("OpenAI API key not set. Using fallback captions.")
                return self._generate_fallback_captions(transcript, visual_analysis)
            
            # Prepare context
            text = transcript.get("text", "No speech detected")
            scene = visual_analysis.get("description", "Unknown scene")
            objects = ", ".join(visual_analysis.get("objects", [])[:5])
            
            context = f"""
            Original transcript: {text}
            Visual context: {scene}
            Objects visible: {objects}
            """
            
            # Generate different caption styles
            styles = {
                "professional": "Create a professional, formal caption suitable for business presentations. Focus on clarity and professionalism.",
                "creative": "Create an engaging, creative caption that tells a story. Use descriptive language and make it interesting.",
                "accessible": "Create a simple, easy-to-understand caption using clear language suitable for all audiences."
            }
            
            captions = {}
            
            for style_name, style_prompt in styles.items():
                try:
                    prompt = f"""
                    {style_prompt}
                    
                    Context: {context}
                    
                    Generate a {style_name} caption (maximum 200 words):
                    """
                    
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are an expert video caption writer."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=200,
                        temperature=0.7
                    )
                    
                    captions[style_name] = response.choices[0].message.content.strip()
                    
                except Exception as e:
                    logger.error(f"Error generating {style_name} caption: {str(e)}")
                    captions[style_name] = self._generate_fallback_caption(transcript, visual_analysis, style_name)
            
            return captions
            
        except Exception as e:
            logger.error(f"Error in caption generation: {str(e)}")
            return self._generate_fallback_captions(transcript, visual_analysis)
    
    def _generate_fallback_captions(self, transcript: Dict, visual_analysis: Dict) -> Dict[str, str]:
        """Generate fallback captions when OpenAI is not available"""
        text = transcript.get("text", "No speech detected")
        scene = visual_analysis.get("scene_type", "unknown").replace("_", " ")
        
        return {
            "professional": f"This video presents content in a {scene} setting. {text}",
            "creative": f"Welcome to this engaging presentation taking place in a {scene}. {text}",
            "accessible": f"This video shows a {scene}. The speaker says: {text}"
        }
    
    def _generate_fallback_caption(self, transcript: Dict, visual_analysis: Dict, style: str) -> str:
        """Generate single fallback caption"""
        text = transcript.get("text", "No speech detected")
        scene = visual_analysis.get("scene_type", "unknown").replace("_", " ")
        
        if style == "professional":
            return f"This video presents content in a {scene} setting. {text}"
        elif style == "creative":
            return f"Step into this {scene} where {text}"
        else:  # accessible
            return f"Video shows {scene}. Speaker says: {text}"

# Initialize processor
video_processor = VideoProcessor()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Video Caption Enhancement API",
        "status": "running",
        "version": "1.0.0",
        "models_loaded": {
            "whisper": whisper_model is not None,
            "clip": clip_model is not None
        }
    }

@app.post("/process-video")
async def process_video(file: UploadFile = File(...)):
    """Process uploaded video and return enhanced captions"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    logger.info(f"Processing video: {file.filename}")
    
    try:
        result = await video_processor.process_video(file)
        return JSONResponse(content=result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "models": {
            "whisper": "loaded" if whisper_model else "not loaded",
            "clip": "loaded" if clip_model else "not loaded"
        },
        "device": device,
        "openai_configured": bool(openai.api_key)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
