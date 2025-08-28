import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return None

def deploy_to_github():
    """Deploy the project to GitHub."""
    print("🚀 Starting GitHub deployment...\n")
    
    # Check if git is installed
    if not run_command("git --version", "Checking Git installation"):
        print("❌ Git is not installed. Please install Git first.")
        return False
    
    # Initialize git repository if not exists
    if not Path(".git").exists():
        run_command("git init", "Initializing Git repository")
    
    # Create .gitignore if not exists
    if not Path(".gitignore").exists():
        print("📝 Creating .gitignore file...")
        with open(".gitignore", "w") as f:
            f.write("""# Python
__pycache__/
*.py[cod]
*.so
.Python
build/
dist/
*.egg-info/

# Virtual Environment
venv/
env/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.temp
*.log

# Model files (too large)
*.pt
*.pth
*.bin

# Video files
*.mp4
*.avi
*.mov

# Audio files
*.wav
*.mp3

# Environment variables
.env
""")
    
    # Add files to git
    run_command("git add .", "Adding files to repository")
    
    # Create initial commit
    run_command('git commit -m "Initial commit: Multimodal Video Caption Enhancement System"', 
                "Creating initial commit")
    
    print("\n✅ Project prepared for GitHub!")
    print("\n📋 Next steps:")
    print("1. Create a new repository on GitHub.com")
    print("2. Copy the repository URL")
    print("3. Run these commands:")
    print("   git remote add origin <your-repo-url>")
    print("   git branch -M main")
    print("   git push -u origin main")
    print("\n🔗 Example:")
    print("   git remote add origin https://github.com/YOUR_USERNAME/video-caption-enhancement.git")
    print("   git branch -M main")
    print("   git push -u origin main")

if __name__ == "__main__":
    deploy_to_github()