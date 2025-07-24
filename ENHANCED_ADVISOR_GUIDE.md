# Enhanced AI Advisor - User Guide

## 🚀 Quick Start

### Option 1: Easy Startup (Recommended)
```bash
python start_advisor.py
```

### Option 2: Direct Streamlit
```bash
streamlit run enhanced_main.py
```

### Option 3: Test First
```bash
python test_enhanced_main.py  # Verify everything works
streamlit run enhanced_main.py
```

## 📋 Application Structure

The Enhanced AI Advisor now has **3 main sections** as requested:

### 1. 🤖 AI Consultation
- **Purpose**: Get AI project advice and consultation
- **Features**:
  - Multiple consultation types (General, RAG vs Fine-tuning, Cybersecurity, etc.)
  - Context-aware advice using your knowledge base
  - Model selection (supports multiple Ollama models)
  - Conversation history and export
  - Source attribution for all advice

### 2. 📚 AI Learning
- **Purpose**: Personalized learning paths and skill development
- **Features**:
  - Pre-defined learning paths (Beginner to Advanced)
  - Custom learning path creation
  - Skill level assessment
  - Progress tracking
  - Resource recommendations from your knowledge base
  - Video sequences and supplementary reading

### 3. 📊 Project Management
- **Purpose**: Track and manage your AI projects
- **Features**:
  - Create and manage multiple projects
  - Progress tracking with visual indicators
  - Project-specific AI advice
  - Analytics and insights
  - Timeline and priority management
  - Technology stack tracking

## 📊 Resource Breakdown (Sidebar)

The sidebar now shows a **detailed breakdown** of your knowledge resources:

### 📹 YouTube Videos
- Count of video resources
- Number of knowledge chunks from videos

### 📰 Daily.dev Articles  
- Count of Daily.dev articles
- Number of knowledge chunks from articles

### 📄 Other Resources
- Any other content types
- Associated knowledge chunks

### 📈 Total Summary
- **Total Resources**: Combined count of all resources
- **Total Chunks**: All knowledge chunks across all sources

## 🔧 Technical Details

### Knowledge Base Structure
The application automatically detects and handles:
- **Unified format**: New integrated Daily.dev + YouTube structure
- **Legacy format**: Original YouTube-only knowledge base
- **Mixed sources**: Properly categorizes content by source type

### Search Capabilities
- **Keyword search**: Traditional text matching
- **Relevance scoring**: Intelligent ranking of results
- **Source attribution**: Shows whether content came from YouTube or Daily.dev
- **Context-aware**: Uses search results to provide better AI advice

### Model Support
- **Multiple models**: Switch between different Ollama models
- **Fallback handling**: Graceful degradation if models aren't available
- **Performance optimization**: Efficient model usage and caching

## 🛠️ Requirements

### Required Dependencies
```bash
pip install streamlit ollama pathlib
```

### Optional Dependencies
```bash
pip install sentence-transformers  # For enhanced search
pip install chromadb              # For vector search
```

### Ollama Setup
1. Install Ollama: https://ollama.ai/
2. Start Ollama: `ollama serve`
3. Install a model: `ollama pull llama2`

## 📁 File Structure

```
AI_ADVISOR/
├── enhanced_main.py           # Main application
├── start_advisor.py          # Easy startup script
├── test_enhanced_main.py     # Test script
├── ENHANCED_ADVISOR_GUIDE.md # This guide
├── data/
│   └── unified_knowledge_base.json  # Unified knowledge base
├── knowledge_base_final.json       # Legacy knowledge base
└── src/                            # Source modules
    ├── education/
    ├── project_management/
    └── resources/
```

## 🎯 Usage Examples

### Getting AI Consultation
1. Select "🤖 AI Consultation"
2. Choose consultation type (e.g., "RAG vs Fine-tuning Decision")
3. Describe your project
4. Get personalized advice with source references

### Creating Learning Path
1. Select "📚 AI Learning"
2. Choose learning focus (e.g., "Deep Learning & Neural Networks")
3. Set your skill level
4. Generate personalized learning sequence

### Managing Projects
1. Select "📊 Project Management"
2. Create new project with details
3. Track progress and get AI recommendations
4. View analytics and insights

## 🔍 Troubleshooting

### "No Ollama models found"
```bash
ollama pull llama2
# or
ollama pull mistral
```

### "Knowledge base not found"
- Check if `data/unified_knowledge_base.json` or `knowledge_base_final.json` exists
- Run the Daily.dev scraper to populate content

### "Import errors"
```bash
pip install streamlit ollama
```

### "Port already in use"
```bash
streamlit run enhanced_main.py --server.port 8503
```

## 🎉 Features Summary

✅ **3 Main Sections**: AI Consultation, AI Learning, Project Management  
✅ **Resource Breakdown**: YouTube videos, Daily.dev articles, other sources  
✅ **Total Chunk Count**: Comprehensive knowledge base statistics  
✅ **Source Attribution**: Know where advice comes from  
✅ **Progress Tracking**: Learning and project progress  
✅ **Multiple Models**: Support for different Ollama models  
✅ **Export Capabilities**: Save conversations and project data  
✅ **Responsive Design**: Clean, organized interface  

The application is now properly structured with the 3 sections you requested and provides detailed resource breakdowns in the sidebar!