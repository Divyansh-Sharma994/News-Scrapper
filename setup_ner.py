"""
Setup script for NER Entity Extraction
Installs spaCy and downloads the required language model
"""

import subprocess
import sys

def install_spacy():
    """Install spaCy package"""
    print("📦 Installing spaCy...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "spacy>=3.7.0"])
        print("✅ spaCy installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing spaCy: {e}")
        return False

def download_model():
    """Download spaCy English model"""
    print("📥 Downloading spaCy English model (en_core_web_sm)...")
    try:
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        print("✅ Model downloaded successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error downloading model: {e}")
        return False

def verify_installation():
    """Verify that spaCy and model are properly installed"""
    print("🔍 Verifying installation...")
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        print("✅ spaCy is working correctly!")
        print(f"   Model: {nlp.meta['name']} v{nlp.meta['version']}")
        return True
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    print("=" * 60)
    print("NER Entity Extraction Setup")
    print("=" * 60)
    print()
    
    # Step 1: Install spaCy
    if not install_spacy():
        print("\n⚠️  Setup failed. Please install spaCy manually:")
        print("   pip install spacy>=3.7.0")
        return
    
    print()
    
    # Step 2: Download model
    if not download_model():
        print("\n⚠️  Model download failed. Please download manually:")
        print("   python -m spacy download en_core_web_sm")
        return
    
    print()
    
    # Step 3: Verify
    if verify_installation():
        print()
        print("=" * 60)
        print("🎉 Setup completed successfully!")
        print("=" * 60)
        print()
        print("You can now use the NER entity extraction feature.")
        print("Run the app with: streamlit run app2.py")
    else:
        print("\n⚠️  Setup completed but verification failed.")
        print("   Please check the error messages above.")

if __name__ == "__main__":
    main()
