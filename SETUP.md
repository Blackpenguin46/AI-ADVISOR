# AI Advisor Setup Guide

Complete setup instructions for getting your AI project advisor running locally.

## 🎯 Quick Setup (5 Minutes)

### Prerequisites
- **Operating System**: Windows 10+, macOS 10.15+, or Linux
- **Python**: 3.8 or higher ([Download Python](https://python.org/downloads/))
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 5GB free space (for models and dependencies)

### Step 1: Install Ollama
Ollama provides the local AI model serving capability.

**macOS/Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download installer from [ollama.ai](https://ollama.ai/download)

**Verify Installation:**
```bash
ollama --version
```

### Step 2: Download AI Model
Install a local language model (choose one):

**Recommended (Fast):**
```bash
ollama pull llama2        # 3.8GB - Good balance of speed/quality
```

**Alternative Options:**
```bash
ollama pull mistral       # 4.1GB - Better performance
ollama pull codellama     # 3.8GB - Better for code-related queries
ollama pull llama2:13b    # 7.3GB - Higher quality responses
```

### Step 3: Clone Repository
```bash
git clone https://github.com/Blackpenguin46/AI-ADVISOR.git
cd AI-ADVISOR
```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Start AI Advisor
```bash
streamlit run main.py
```

🎉 **Done!** Your AI Advisor will open at http://localhost:8501

## 📋 Detailed Setup Instructions

### System Requirements

**Minimum Requirements:**
- Python 3.8+
- 4GB RAM
- 5GB free storage
- Internet connection (for initial model download)

**Recommended Requirements:**
- Python 3.10+
- 8GB RAM
- 10GB free storage
- Fast internet for quicker model downloads

### Python Environment Setup

**Option 1: Using Conda (Recommended)**
```bash
# Create isolated environment
conda create -n ai-advisor python=3.10
conda activate ai-advisor

# Install dependencies
pip install -r requirements.txt
```

**Option 2: Using venv**
```bash
# Create virtual environment
python -m venv ai-advisor-env

# Activate environment
# On Windows:
ai-advisor-env\Scripts\activate
# On macOS/Linux:
source ai-advisor-env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Option 3: System Python (Not Recommended)**
```bash
pip install -r requirements.txt
```

### Ollama Detailed Setup

**1. Install Ollama Service**

*macOS:*
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

*Windows:*
- Download from [ollama.ai/download](https://ollama.ai/download)
- Run installer as administrator
- Restart terminal after installation

*Linux:*
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**2. Start Ollama Service**
```bash
ollama serve
```
*Keep this running in a separate terminal*

**3. Download Models**

*Quick Start Model:*
```bash
ollama pull llama2
```

*For Better Performance:*
```bash
ollama pull mistral
```

*For Code-Heavy Queries:*
```bash
ollama pull codellama
```

**4. Verify Models**
```bash
ollama list
```

### Dependency Installation

**Core Dependencies (requirements.txt):**
```
streamlit>=1.28.0
ollama>=0.1.0
pathlib
json5
```

**Install Command:**
```bash
pip install -r requirements.txt
```

**Manual Installation (if needed):**
```bash
pip install streamlit ollama
```

### Configuration Options

**Model Selection:**
Edit the default model in `main.py` if desired:
```python
# Line 78 in main.py
def __init__(self, model_name="llama2", knowledge_base=None):
```

**Available Models:**
- `llama2` - Balanced performance (default)
- `mistral` - Better quality responses  
- `codellama` - Optimized for code
- `llama2:13b` - Highest quality (requires more RAM)

### Troubleshooting Common Issues

**Issue: "ollama command not found"**
```bash
# Solution: Add Ollama to PATH or reinstall
export PATH=$PATH:/usr/local/bin
# Or restart terminal after installation
```

**Issue: "Model not found"**
```bash
# Solution: Download the model first
ollama pull llama2
ollama list  # Verify it's installed
```

**Issue: "Connection refused to Ollama"**
```bash
# Solution: Start Ollama service
ollama serve
# Keep this running in background
```

**Issue: "Memory error during startup"**
```bash
# Solution: Use smaller model
ollama pull llama2  # Instead of llama2:13b
# Or close other applications to free memory
```

**Issue: "Streamlit not found"**
```bash
# Solution: Install Streamlit
pip install streamlit
# Or reinstall all dependencies
pip install -r requirements.txt
```

**Issue: "Knowledge base not found"**
```bash
# Solution: Ensure you're in correct directory
ls knowledge_base_final.json  # Should exist
# If missing, re-download repository
```

### Advanced Configuration

**Custom Model Configuration:**
Create `.env` file:
```bash
OLLAMA_MODEL=mistral
STREAMLIT_PORT=8501
STREAMLIT_HOST=localhost
```

**Memory Optimization:**
For systems with limited RAM, use smaller models:
```bash
ollama pull tinyllama  # 637MB - Very fast but lower quality
```

**Performance Tuning:**
Adjust chunk size for better performance in `main.py`:
```python
# Modify line ~67 for different response speeds
total_chunks = sum(v.get('chunk_count', 0) for v in self.knowledge_db.values())
```

### Network Configuration

**Firewall Settings:**
Ensure ports are open:
- Port 8501 (Streamlit)
- Port 11434 (Ollama API)

**Corporate Networks:**
If behind corporate firewall:
```bash
# Set proxy for pip
pip install --proxy http://proxy:port streamlit ollama

# Set proxy for Ollama (if needed)
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=http://proxy:port
```

### Verification Steps

**1. Test Python Environment**
```bash
python --version  # Should be 3.8+
pip list | grep streamlit  # Should show streamlit
```

**2. Test Ollama**
```bash
ollama list  # Should show installed models
ollama run llama2 "Hello"  # Should generate response
```

**3. Test AI Advisor**
```bash
streamlit run main.py
# Should open browser to http://localhost:8501
# Should show "80 videos" in sidebar
```

## 🚀 Alternative Installation Methods

### Docker Installation (Advanced)
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

EXPOSE 8501
CMD ["streamlit", "run", "main.py"]
```

### Cloud Deployment (VPS/Cloud Server)
```bash
# On cloud instance
git clone https://github.com/Blackpenguin46/AI-ADVISOR.git
cd AI-ADVISOR
pip install -r requirements.txt

# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama2

# Run with external access
streamlit run main.py --server.address=0.0.0.0
```

### Automated Script Installation
Create `install.sh`:
```bash
#!/bin/bash
set -e

echo "Installing AI Advisor..."

# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Download model
ollama pull llama2 &

# Install Python dependencies
pip install -r requirements.txt

# Wait for model download
wait

echo "Setup complete! Run: streamlit run main.py"
```

Make executable and run:
```bash
chmod +x install.sh
./install.sh
```

## 📱 Usage After Setup

### Starting the System
```bash
# 1. Ensure Ollama is running (in separate terminal)
ollama serve

# 2. Start AI Advisor (in project directory)
streamlit run main.py
```

### First Use
1. Open http://localhost:8501
2. Verify "80 videos" shows in sidebar
3. Select consultation type
4. Ask your first question!

### Daily Usage
```bash
# Quick start (if Ollama already running)
streamlit run main.py
```

## 🔧 Maintenance

### Updating Models
```bash
# Update to newer model versions
ollama pull llama2:latest
ollama rm llama2:old  # Remove old version
```

### Updating Dependencies
```bash
pip install --upgrade streamlit ollama
```

### Backing Up Configuration
```bash
# Save your setup
cp knowledge_base_final.json backup/
cp main.py backup/
```

---

**Need Help?** 
- Check troubleshooting section above
- Verify all prerequisites are met
- Ensure Ollama service is running
- Test with minimal model (tinyllama) if memory limited

**Ready to Start?** Run `streamlit run main.py` and begin consulting with your AI advisor!