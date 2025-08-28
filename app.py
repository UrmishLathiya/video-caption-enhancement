"""
Multimodal Video Caption Enhancement System - Streamlit Frontend
Author: AI Assistant
Date: August 28, 2025
"""

import streamlit as st
import requests
import json
import time
import os
from pathlib import Path
import tempfile
from typing import Dict, Any

# Page configuration
st.set_page_config(
    page_title="Video Caption Enhancement",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 10px;
    }
    
    .metric-container {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .caption-box {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #28a745;
    }
    
    .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #dc3545;
    }
    
    .processing-spinner {
        text-align: center;
        padding: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
API_URL = "http://localhost:8000"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

class VideoProcessorUI:
    """Main UI class for the video processing application"""
    
    def __init__(self):
        self.api_url = API_URL
        
    def render_header(self):
        """Render the main header"""
        st.markdown("""
        <div class="main-header">
            <h1>🎬 Video Caption Enhancement System</h1>
            <p>AI-powered multimodal video analysis with speech recognition and visual understanding</p>
        </div>
        """, unsafe_allow_html=True)
        
    def render_sidebar(self):
        """Render the sidebar with information and controls"""
        with st.sidebar:
            st.header("🔧 System Information")
            
            # Check API health
            health_status = self.check_api_health()
            
            if health_status:
                st.markdown('<div class="success-message">✅ API is running</div>', unsafe_allow_html=True)
                
                # Display model status
                st.subheader("📊 Model Status")
                models = health_status.get("models", {})
                
                col1, col2 = st.columns(2)
                with col1:
                    whisper_status = "✅" if models.get("whisper") == "loaded" else "❌"
                    st.write(f"Whisper: {whisper_status}")
                    
                with col2:
                    clip_status = "✅" if models.get("clip") == "loaded" else "❌"
                    st.write(f"CLIP: {clip_status}")
                
                # Device info
                device = health_status.get("device", "unknown")
                st.write(f"**Device:** {device}")
                
                # OpenAI status
                openai_status = "✅" if health_status.get("openai_configured") else "⚠️"
                st.write(f"**OpenAI:** {openai_status}")
                
                if not health_status.get("openai_configured"):
                    st.warning("Set OPENAI_API_KEY environment variable for enhanced captions")
                    
            else:
                st.markdown('<div class="error-message">❌ API not running</div>', unsafe_allow_html=True)
                st.error("Please start the FastAPI backend first")
                
            st.divider()
            
            # File requirements
            st.subheader("📋 Requirements")
            st.write("**Supported formats:** MP4, MOV, AVI")
            st.write("**Max file size:** 100MB")
            st.write("**Max duration:** 2 minutes")
            st.write("**Optimal:** Clear audio, good lighting")
            
            st.divider()
            
            # About section
            st.subheader("ℹ️ About")
            st.write("""
            This system combines:
            - **Whisper** for speech recognition
            - **CLIP** for visual analysis  
            - **GPT-3.5** for caption enhancement
            - **FastAPI** backend
            - **Streamlit** frontend
            """)
    
    def check_api_health(self):
        """Check if the API is running and healthy"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.RequestException:
            pass
        return None
    
    def validate_file(self, uploaded_file):
        """Validate uploaded file"""
        if uploaded_file is None:
            return False, "Please upload a video file"
            
        # Check file size
        if uploaded_file.size > MAX_FILE_SIZE:
            return False, f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB"
        
        # Check file extension
        file_extension = Path(uploaded_file.name).suffix.lower()
        if file_extension not in ['.mp4', '.mov', '.avi']:
            return False, "Unsupported file format. Please upload MP4, MOV, or AVI files."
        
        return True, "File is valid"
    
    def process_video(self, uploaded_file):
        """Send video to API for processing"""
        try:
            # Prepare file for upload
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            
            # Send request
            with st.spinner("🔄 Processing video... This may take a few minutes."):
                response = requests.post(
                    f"{self.api_url}/process-video",
                    files=files,
                    timeout=300  # 5 minutes timeout
                )
            
            if response.status_code == 200:
                return True, response.json()
            else:
                error_detail = response.json().get("detail", "Unknown error")
                return False, f"API Error: {error_detail}"
                
        except requests.exceptions.Timeout:
            return False, "Processing timeout. Please try with a shorter video."
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def render_upload_section(self):
        """Render the file upload section"""
        st.header("📤 Upload Video")
        
        uploaded_file = st.file_uploader(
            "Choose a video file",
            type=['mp4', 'mov', 'avi'],
            help="Upload a video file (MP4, MOV, or AVI) up to 100MB and 2 minutes long"
        )
        
        if uploaded_file:
            # Validate file
            is_valid, message = self.validate_file(uploaded_file)
            
            if is_valid:
                st.success(f"✅ {message}")
                
                # Display file info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("File Name", uploaded_file.name)
                with col2:
                    st.metric("File Size", f"{uploaded_file.size / (1024*1024):.1f} MB")
                with col3:
                    st.metric("File Type", uploaded_file.type)
                
                # Process button
                if st.button("🚀 Process Video", type="primary", use_container_width=True):
                    success, result = self.process_video(uploaded_file)
                    
                    if success:
                        st.session_state.processing_result = result
                        st.session_state.show_results = True
                        st.rerun()
                    else:
                        st.error(f"❌ {result}")
                        
            else:
                st.error(f"❌ {message}")
        
        return uploaded_file
    
    def render_results(self, result: Dict[str, Any]):
        """Render processing results"""
        st.header("📊 Processing Results")
        
        # Processing summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            duration = result.get("video_info", {}).get("duration", 0)
            st.metric("Video Duration", f"{duration:.1f}s")
            
        with col2:
            confidence = result.get("transcript", {}).get("confidence", 0)
            st.metric("Speech Confidence", f"{confidence:.1%}")
            
        with col3:
            processing_time = result.get("processing_time", 0)
            st.metric("Processing Time", f"{processing_time:.1f}s")
            
        with col4:
            frame_count = result.get("visual_analysis", {}).get("frame_count", 0)
            st.metric("Frames Analyzed", str(frame_count))
        
        # Tabs for different results
        tab1, tab2, tab3, tab4 = st.tabs(["🎙️ Transcript", "👁️ Visual Analysis", "✨ Enhanced Captions", "📄 Raw Data"])
        
        with tab1:
            self.render_transcript_tab(result.get("transcript", {}))
            
        with tab2:
            self.render_visual_tab(result.get("visual_analysis", {}))
            
        with tab3:
            self.render_captions_tab(result.get("enhanced_captions", {}), result)
            
        with tab4:
            self.render_raw_data_tab(result)
    
    def render_transcript_tab(self, transcript: Dict[str, Any]):
        """Render transcript results"""
        st.subheader("🎙️ Speech Recognition Results")
        
        text = transcript.get("text", "No speech detected")
        confidence = transcript.get("confidence", 0)
        language = transcript.get("language", "unknown")
        
        if text:
            # Main transcript
            st.markdown(f"**Language:** {language.upper()}")
            st.markdown(f"**Overall Confidence:** {confidence:.1%}")
            
            st.markdown("### Full Transcript")
            st.markdown(f'<div class="caption-box">{text}</div>', unsafe_allow_html=True)
            
            # Segments timeline
            segments = transcript.get("segments", [])
            if segments:
                st.markdown("### Timeline Segments")
                
                for i, segment in enumerate(segments):
                    start = segment.get("start", 0)
                    end = segment.get("end", 0)
                    seg_text = segment.get("text", "")
                    seg_confidence = segment.get("confidence", 0)
                    
                    with st.expander(f"Segment {i+1}: {start:.1f}s - {end:.1f}s (Confidence: {seg_confidence:.1%})"):
                        st.write(seg_text)
        else:
            st.info("No speech was detected in this video.")
    
    def render_visual_tab(self, visual_analysis: Dict[str, Any]):
        """Render visual analysis results"""
        st.subheader("👁️ Visual Scene Analysis")
        
        scene_type = visual_analysis.get("scene_type", "unknown")
        objects = visual_analysis.get("objects", [])
        description = visual_analysis.get("description", "")
        
        # Scene information
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Scene Type:**")
            st.markdown(f'<div class="metric-container">{scene_type.replace("_", " ").title()}</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown("**Objects Detected:**")
            if objects:
                objects_text = ", ".join(objects[:8])  # Show first 8 objects
                st.markdown(f'<div class="metric-container">{objects_text}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="metric-container">No objects detected</div>', unsafe_allow_html=True)
        
        # Scene description
        if description:
            st.markdown("**Scene Description:**")
            st.markdown(f'<div class="caption-box">{description}</div>', unsafe_allow_html=True)
        
        # Individual frame analysis (if available)
        individual_frames = visual_analysis.get("individual_frames", [])
        if individual_frames:
            st.markdown("### Individual Frame Analysis")
            
            for i, frame_analysis in enumerate(individual_frames[:3]):  # Show first 3 frames
                with st.expander(f"Frame {i+1} Analysis"):
                    frame_scene = frame_analysis.get("scene_type", "unknown")
                    frame_objects = frame_analysis.get("objects", [])
                    frame_desc = frame_analysis.get("description", "")
                    
                    st.write(f"**Scene:** {frame_scene.replace('_', ' ')}")
                    st.write(f"**Objects:** {', '.join(frame_objects[:5])}")
                    st.write(f"**Description:** {frame_desc}")
    
    def render_captions_tab(self, enhanced_captions: Dict[str, str], result: Dict[str, Any]):
        """Render enhanced captions"""
        st.subheader("✨ AI-Enhanced Captions")
        
        if not enhanced_captions:
            st.info("No enhanced captions available.")
            return
        
        # Professional caption
        if "professional" in enhanced_captions:
            st.markdown("### 📊 Professional Style")
            st.markdown(f'<div class="caption-box">{enhanced_captions["professional"]}</div>', unsafe_allow_html=True)
        
        # Creative caption
        if "creative" in enhanced_captions:
            st.markdown("### 🎨 Creative Style")
            st.markdown(f'<div class="caption-box">{enhanced_captions["creative"]}</div>', unsafe_allow_html=True)
        
        # Accessible caption
        if "accessible" in enhanced_captions:
            st.markdown("### ♿ Accessible Style")
            st.markdown(f'<div class="caption-box">{enhanced_captions["accessible"]}</div>', unsafe_allow_html=True)
        
        # Download options
        st.markdown("### 💾 Download Options")
        
        # Prepare download data
        download_data = {
            "enhanced_captions": enhanced_captions,
            "timestamp": result.get("timestamp", ""),
            "video_info": result.get("video_info", {})
        }
        
        col1, col2 = st.columns(2)
        
        with col1:
            # JSON download
            json_data = json.dumps(download_data, indent=2)
            st.download_button(
                label="📄 Download as JSON",
                data=json_data,
                file_name="enhanced_captions.json",
                mime="application/json"
            )
        
        with col2:
            # Text download
            text_data = "\n\n".join([
                f"=== {style.upper()} STYLE ===\n{caption}"
                for style, caption in enhanced_captions.items()
            ])
            st.download_button(
                label="📝 Download as Text",
                data=text_data,
                file_name="enhanced_captions.txt",
                mime="text/plain"
            )
    
    def render_raw_data_tab(self, result: Dict[str, Any]):
        """Render raw JSON data"""
        st.subheader("📄 Raw Processing Data")
        st.json(result)
    
    def render_sample_videos_section(self):
        """Render sample videos section"""
        with st.expander("🎬 Sample Videos & Tips"):
            st.markdown("""
            ### 📋 Testing Tips
            
            **Good test videos should have:**
            - Clear speech (not too fast, minimal background noise)
            - Good lighting and stable camera
            - Duration between 30 seconds to 2 minutes
            - Single speaker preferred for ASR accuracy
            
            **Example scenarios to test:**
            - Business presentation
            - Educational content
            - Product demonstration  
            - Interview or conversation
            - Outdoor scene with narration
            
            **Common issues:**
            - Very quiet audio → Low transcription confidence
            - Fast speech → Potential word errors
            - Multiple speakers → Mixed transcription
            - Poor lighting → Less accurate visual analysis
            """)
    
    def run(self):
        """Main application runner"""
        # Initialize session state
        if 'show_results' not in st.session_state:
            st.session_state.show_results = False
        if 'processing_result' not in st.session_state:
            st.session_state.processing_result = None
        
        # Render components
        self.render_header()
        self.render_sidebar()
        
        # Main content area
        if not self.check_api_health():
            st.error("🚨 **API Server Not Running**")
            st.markdown("""
            Please start the FastAPI backend first:
            
            ```bash
            python main.py
            ```
            
            Or run with uvicorn:
            
            ```bash
            uvicorn main:app --host 0.0.0.0 --port 8000
            ```
            """)
            return
        
        # Show results if available
        if st.session_state.show_results and st.session_state.processing_result:
            # Clear results button
            if st.button("🔄 Process New Video", type="secondary"):
                st.session_state.show_results = False
                st.session_state.processing_result = None
                st.rerun()
            
            # Show results
            self.render_results(st.session_state.processing_result)
            
        else:
            # Upload section
            uploaded_file = self.render_upload_section()
            
            # Sample videos section
            self.render_sample_videos_section()

# Main application
if __name__ == "__main__":
    app = VideoProcessorUI()
    app.run()
