"""
System Status Checker - Quick diagnostic tool
"""

import requests
import subprocess
import sys
from datetime import datetime

def check_services():
    print("🔍 Video Caption Enhancement System - Status Check")
    print("=" * 60)
    print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check FastAPI Backend
    print("🚀 Checking FastAPI Backend (http://localhost:8000)...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ FastAPI Backend: RUNNING")
            print(f"   - Models: Whisper={data['models']['whisper']}, CLIP={data['models']['clip']}")
            print(f"   - Device: {data['device']}")
            print(f"   - OpenAI: {'Yes' if data['openai_configured'] else 'No (fallback mode)'}")
        else:
            print(f"❌ FastAPI Backend: ERROR (Status: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print("❌ FastAPI Backend: NOT RUNNING")
        print("   ➤ Start with: python main.py")
    except Exception as e:
        print(f"❌ FastAPI Backend: ERROR - {e}")
    
    print()
    
    # Check Streamlit Frontend
    print("🌐 Checking Streamlit Frontend (http://localhost:8502)...")
    try:
        response = requests.get("http://localhost:8502/healthz", timeout=5)
        print("✅ Streamlit Frontend: RUNNING")
    except requests.exceptions.ConnectionError:
        print("❌ Streamlit Frontend: NOT RUNNING")
        print("   ➤ Start with: streamlit run app.py --server.port=8502")
    except Exception as e:
        # Streamlit doesn't have healthz, try a different approach
        try:
            response = requests.get("http://localhost:8502", timeout=5)
            if response.status_code == 200:
                print("✅ Streamlit Frontend: RUNNING")
            else:
                print(f"❌ Streamlit Frontend: ERROR (Status: {response.status_code})")
        except:
            print("❌ Streamlit Frontend: NOT RUNNING")
            print("   ➤ Start with: streamlit run app.py --server.port=8502")
    
    print()
    print("=" * 60)
    
    # Summary
    try:
        api_ok = requests.get("http://localhost:8000/health", timeout=2).status_code == 200
        frontend_ok = requests.get("http://localhost:8502", timeout=2).status_code == 200
        
        if api_ok and frontend_ok:
            print("🎉 System Status: ALL SERVICES RUNNING")
            print("🌐 Frontend URL: http://localhost:8502")
            print("📡 API URL: http://localhost:8000")
            print("📚 API Docs: http://localhost:8000/docs")
        elif api_ok:
            print("⚠️  System Status: API ONLY (Frontend down)")
        elif frontend_ok:
            print("⚠️  System Status: FRONTEND ONLY (API down)")
        else:
            print("❌ System Status: ALL SERVICES DOWN")
            print("\n🔧 Quick Fix:")
            print("1. Start API: python main.py")
            print("2. Start Frontend: streamlit run app.py --server.port=8502")
            
    except:
        print("❌ System Status: CANNOT DETERMINE")

if __name__ == "__main__":
    check_services()
