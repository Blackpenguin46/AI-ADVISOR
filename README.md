# 🚀 AI Advisor - Enhanced Knowledge-Based AI Consultation System

Your comprehensive AI consultant with multi-format resource support and Daily.dev integration.

## ⚡ Quick Start

### 1. Setup (First Time Only)
```bash
python setup.py
```

### 2. Run AI Advisor
```bash
python run.py
```

That's it! 🎉 Your browser will open automatically at http://localhost:8501

## 🎯 Features

### 🧠 **AI Consultation**
- Expert advice on AI projects and implementation
- RAG vs Fine-tuning decision support
- Technology stack recommendations
- Project planning and troubleshooting

### 📚 **Learning System**
- Personalized AI lessons based on your questions
- Structured explanations with examples
- Interactive follow-up questions
- Progress tracking

### 📊 **Project Management**
- AI project templates (RAG, Computer Vision, etc.)
- Task tracking with Kanban boards
- Milestone management
- Team coordination tools

### 📁 **Multi-Format Knowledge Base**
- **80 AI educational videos** (built-in)
- **PDF uploads** - Research papers, documentation
- **DOCX files** - Reports, guides
- **Web URLs** - Articles, blog posts
- **Daily.dev integration** - Latest tech articles

### 📰 **Daily.dev Integration**
- **Basic Sync** - Manual article fetching
- **Comprehensive Scraping** - Get ALL daily.dev articles
- **Scheduled Sync** - Automatic background updates

## 📋 Prerequisites

- **Python 3.8+**
- **Ollama** with an AI model (download from https://ollama.ai)
- **Chrome browser** (for Daily.dev scraping)

## 🛠️ Installation

### Option 1: Automatic Setup
```bash
python setup.py
python run.py
```

### Option 2: Manual Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Install Daily.dev features (optional)
pip install mcp selenium webdriver-manager fastmcp

# Run the application
streamlit run enhanced_main.py
```

## 🏗️ Project Structure

```
AI_ADVISOR/
├── run.py                          # Simple startup script
├── setup.py                        # Automatic dependency installation
├── enhanced_main.py                # Main application
├── daily_dev_mcp_server.py        # Daily.dev scraper (MCP server)
├── requirements.txt                # Python dependencies
├── knowledge_base_final.json      # 80 AI videos knowledge base
├── data/                          # Data storage
│   ├── unified_knowledge_base.json # All resources combined
│   └── ...
└── src/                           # Source code
    ├── education/                 # Learning system
    ├── project_management/        # Project tracking
    ├── resources/                 # Knowledge base management
    └── ...
```

## 🚀 Usage

### 1. **AI Consultation**
- Select consultation type (RAG vs Fine-tuning, Project Planning, etc.)
- Describe your project or question
- Get expert AI advice with source references

### 2. **Learning System**
- Choose AI topic area
- Ask specific learning questions
- Get structured lessons with examples

### 3. **Resource Management**
- Upload PDFs, DOCX files
- Add web URLs for scraping
- Set up Daily.dev automatic sync

### 4. **Project Management**
- Create AI project from templates
- Track tasks and milestones
- Monitor progress and team coordination

## 📰 Daily.dev Setup

The Daily.dev integration automatically scrapes the latest tech articles:

### Prerequisites
```bash
pip install mcp selenium webdriver-manager fastmcp
```

### Features Available
1. **Basic Sync** - Manual article fetching (20-50 articles)
2. **Comprehensive Scraping** - Get ALL articles (thousands)
3. **Scheduled Sync** - Automatic background updates

### Usage
1. Go to **📁 Resource Management** → **📰 Daily.dev**
2. Choose your sync method
3. Configure settings (article limits, intervals, etc.)
4. Start syncing!

## 🔧 Troubleshooting

### Common Issues

**"Ollama not found"**
- Install Ollama from https://ollama.ai
- Run: `ollama pull llama2`

**"Chrome driver error"**
- Install Chrome browser
- The system auto-downloads ChromeDriver

**"Dependencies missing"**
- Run: `python setup.py` to auto-install
- Or: `pip install -r requirements.txt`

**"Knowledge base error"**
- Check that `knowledge_base_final.json` exists
- The system will auto-create unified knowledge base

## 📊 Performance

### Expected Results
- **Knowledge Base**: 80 videos + your added resources
- **Daily.dev Sync**: 20-50 articles per sync (basic) or thousands (comprehensive)
- **Response Time**: 2-10 seconds for AI consultation
- **Storage**: ~500MB for full knowledge base with Daily.dev articles

### Resource Usage
- **Memory**: 500MB-2GB depending on knowledge base size
- **Disk**: 100MB-1GB for knowledge base and data
- **Network**: Only during Daily.dev sync and article fetching

## 🆘 Support

### Getting Help
1. Check the **Knowledge Explorer** for existing solutions
2. Use the **AI Consultation** to ask about specific issues
3. Review logs in the Streamlit interface
4. Check Ollama status: `ollama list`

### Common Commands
```bash
# Check system status
python diagnostic.py

# Reset knowledge base
rm -rf data/unified_knowledge_base.json

# Update dependencies
pip install -r requirements.txt --upgrade

# Check Ollama models
ollama list
```

## 🎯 Next Steps

After setup, try:

1. **Ask an AI question** in the consultation tab
2. **Take a lesson** in the learning system
3. **Upload a PDF** to expand your knowledge base
4. **Create a project** using the project management tools
5. **Set up Daily.dev sync** for latest tech articles

---

**Your AI advisor is ready to help with any AI project! 🚀**