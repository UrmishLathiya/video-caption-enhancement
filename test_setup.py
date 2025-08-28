"""
Quick Setup Verification Script
Run this to check if all dependencies are properly installed
"""

import sys
import importlib
import subprocess
from pathlib import Path

def check_import(module_name, description=""):
    """Check if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {module_name} - {description}")
        return True
    except ImportError as e:
        print(f"❌ {module_name} - {description} - Error: {e}")
        return False

def check_models():
    """Check if models can be loaded"""
    try:
        print("\n🔍 Testing model loading...")
        
        # Test Whisper
        import whisper
        print("✅ Whisper can be imported")
        
        # Test CLIP
        import clip
        print("✅ CLIP can be imported")
        
        # Test PyTorch
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"✅ PyTorch device: {device}")
        
        return True
    except Exception as e:
        print(f"❌ Model loading error: {e}")
        return False

def main():
    print("🧪 Video Caption Enhancement System - Setup Verification")
    print("=" * 60)
    
    # Check Python version
    print(f"🐍 Python version: {sys.version}")
    
    # Check core dependencies
    print("\n📦 Checking core dependencies:")
    dependencies = [
        ("fastapi", "Web framework"),
        ("uvicorn", "ASGI server"),
        ("streamlit", "Frontend framework"),
        ("whisper", "Speech recognition"),
        ("clip", "Computer vision"),
        ("torch", "Deep learning"),
        ("torchvision", "Computer vision"),
        ("moviepy", "Video processing"),
        ("cv2", "OpenCV - Image processing"),
        ("PIL", "Image library"),
        ("openai", "GPT integration"),
        ("requests", "HTTP client"),
        ("numpy", "Numerical computing")
    ]
    
    success_count = 0
    for module, desc in dependencies:
        if check_import(module, desc):
            success_count += 1
    
    print(f"\n📊 Dependencies: {success_count}/{len(dependencies)} successful")
    
    # Check models
    models_ok = check_models()
    
    # Check OpenAI API key
    import os
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print("✅ OpenAI API key is set")
    else:
        print("⚠️  OpenAI API key not set (enhanced captions will use fallback)")
    
    # Summary
    print("\n" + "=" * 60)
    if success_count == len(dependencies) and models_ok:
        print("🎉 Setup verification PASSED! You're ready to run the system.")
        print("\nNext steps:")
        print("1. Start the backend: python main.py")
        print("2. Start the frontend: streamlit run app.py")
        print("3. Open http://localhost:8501 in your browser")
    else:
        print("❌ Setup verification FAILED! Please check the errors above.")
        print("\nTry running: pip install -r requirements.txt")

if __name__ == "__main__":
    main()
