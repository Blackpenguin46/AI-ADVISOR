#!/usr/bin/env python3

import streamlit as st
import json
import ollama
from pathlib import Path
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add src to path for new modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Try to import enhanced modules with fallbacks
try:
    from education.ai_learning_system import create_ai_learning_dashboard
except ImportError:
    def create_ai_learning_dashboard(session_state):
        st.info("AI Learning module not available. Install required dependencies.")

try:
    from project_management.ai_project_tracker import create_project_management_app
except ImportError:
    def create_project_management_app():
        st.info("Project Management module not available. Install required dependencies.")

try:
    from resources.unified_knowledge_base import UnifiedKnowledgeBase, create_resource_management_interface
except ImportError:
    def create_resource_management_interface():
        st.info("Resource Management module not available. Install required dependencies.")

# Import the new unified RAG pipeline
try:
    from managers.unified_rag_pipeline import UnifiedRAGPipeline
    UNIFIED_RAG_AVAILABLE = True
except ImportError:
    UNIFIED_RAG_AVAILABLE = False
    logger.warning("Unified RAG pipeline not available")

# Simple knowledge base class that uses JSON instead of ChromaDB
class SimpleKnowledgeBase:
    def __init__(self):
        self.knowledge_db = self.load_knowledge_base()
    
    def load_knowledge_base(self):
        """Load the complete knowledge base"""
        # Try unified format first
        unified_kb_file = "data/unified_knowledge_base.json"
        if Path(unified_kb_file).exists():
            with open(unified_kb_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Fall back to old format
        kb_file = "knowledge_base_final.json"
        if Path(kb_file).exists():
            with open(kb_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def search_knowledge(self, query, n_results=5):
        """Search knowledge base and return in ChromaDB format"""
        query_words = query.lower().split()
        results = []
        
        for item_id, item_data in self.knowledge_db.items():
            # Handle unified format
            if 'metadata' in item_data:
                metadata = item_data['metadata']
                content = item_data.get('content', '')
                title = metadata.get('title', '').lower()
                
                # Score based on keyword matches
                score = 0
                for word in query_words:
                    score += title.count(word) * 3
                    score += content.lower().count(word)
                
                if score > 0:
                    # Get relevant chunk
                    chunks = item_data.get('chunks', [])
                    if chunks:
                        # Find best matching chunk
                        best_chunk = chunks[0]
                        for chunk in chunks[:3]:
                            chunk_lower = chunk.lower()
                            if any(word in chunk_lower for word in query_words):
                                best_chunk = chunk
                                break
                    else:
                        best_chunk = content[:500]
                    
                    # Determine display format based on source type
                    source_type = metadata.get('source_type', 'unknown')
                    if source_type == 'video':
                        uploader = metadata.get('author', 'Unknown')
                    else:
                        uploader = metadata.get('original_source', metadata.get('author', 'Daily.dev'))
                    
                    results.append({
                        'content': best_chunk,
                        'metadata': {
                            'title': metadata.get('title', 'Unknown'),
                            'url': metadata.get('source_url', ''),
                            'uploader': uploader,
                            'source_type': source_type
                        },
                        'distance': 1.0 - (score / 100)  # Convert score to distance
                    })
            else:
                # Handle old format (fallback)
                title = item_data.get('title', '').lower()
                transcript = item_data.get('transcript', '').lower()
                
                score = 0
                for word in query_words:
                    score += title.count(word) * 3
                    score += transcript.count(word)
                
                if score > 0:
                    # Get relevant chunk
                    chunks = item_data.get('chunks', [])
                    if chunks:
                        best_chunk = chunks[0]
                        for chunk in chunks[:3]:
                            chunk_lower = chunk.lower()
                            if any(word in chunk_lower for word in query_words):
                                best_chunk = chunk
                                break
                    else:
                        best_chunk = item_data.get('transcript', '')[:500]
                    
                    results.append({
                        'content': best_chunk,
                        'metadata': {
                            'title': item_data.get('title', 'Unknown'),
                            'url': item_id,
                            'uploader': item_data.get('uploader', 'Unknown'),
                            'source_type': 'video'
                        },
                        'distance': 1.0 - (score / 100)
                    })
        
        # Sort by score (lower distance = better match)
        results.sort(key=lambda x: x['distance'])
        return results[:n_results]
    
    def get_stats(self):
        """Get comprehensive knowledge base statistics with source breakdown"""
        stats = {
            'total_resources': len(self.knowledge_db),
            'total_chunks': 0,
            'by_source': {
                'youtube': {'count': 0, 'chunks': 0},
                'dailydev': {'count': 0, 'chunks': 0},
                'other': {'count': 0, 'chunks': 0}
            },
            'topics': []
        }
        
        for item_id, item_data in self.knowledge_db.items():
            # Count chunks
            chunk_count = item_data.get('chunk_count', len(item_data.get('chunks', [])))
            if chunk_count == 0 and 'content' in item_data:
                # Estimate chunks for content without explicit chunk count
                chunk_count = max(1, len(item_data['content']) // 500)
            
            stats['total_chunks'] += chunk_count
            
            # Determine source type and categorize
            if 'metadata' in item_data:
                metadata = item_data['metadata']
                source_type = metadata.get('source_type', 'unknown')
                title = metadata.get('title', 'Unknown')
                
                if source_type == 'video' or 'youtube.com' in metadata.get('source_url', ''):
                    stats['by_source']['youtube']['count'] += 1
                    stats['by_source']['youtube']['chunks'] += chunk_count
                elif source_type == 'article' or 'daily.dev' in metadata.get('original_source', ''):
                    stats['by_source']['dailydev']['count'] += 1
                    stats['by_source']['dailydev']['chunks'] += chunk_count
                else:
                    stats['by_source']['other']['count'] += 1
                    stats['by_source']['other']['chunks'] += chunk_count
                
                stats['topics'].append(title)
            else:
                # Legacy format - assume YouTube video
                title = item_data.get('title', 'Unknown')
                stats['by_source']['youtube']['count'] += 1
                stats['by_source']['youtube']['chunks'] += chunk_count
                stats['topics'].append(title)
        
        return stats


# Simple AI Advisor class
class SimpleAIAdvisor:
    def __init__(self, model_name="llama2", knowledge_base=None):
        self.model_name = model_name
        self.kb = knowledge_base or SimpleKnowledgeBase()
        self.conversation_history = []
    
    def search_relevant_knowledge(self, query, n_results=5):
        """Search knowledge base and format results for LLM context"""
        results = self.kb.search_knowledge(query, n_results)
        
        if not results:
            return "No relevant knowledge found in the video database."
        
        context = "Relevant information from your AI knowledge base:\n\n"
        for i, result in enumerate(results, 1):
            metadata = result['metadata']
            content = result['content']
            
            source_type = metadata.get('source_type', 'video')
            if source_type == 'video':
                context += f"[Source {i}: {metadata['title']} by {metadata['uploader']}]\n"
            else:
                context += f"[Source {i}: {metadata['title']} from {metadata['uploader']}]\n"
            context += f"{content}\n\n"
        
        return context
    
    def generate_advice(self, user_query, project_context=""):
        """Generate AI project advice using local LLM and knowledge base"""
        
        # Search for relevant knowledge
        relevant_context = self.search_relevant_knowledge(user_query)
        
        # Build the prompt
        system_prompt = """You are an expert AI project advisor with comprehensive knowledge from multiple sources including educational videos, technical articles, and documentation covering AI concepts, frameworks, and implementation strategies.

Your knowledge base includes:
- YouTube educational videos from AI experts and technology companies
- Daily.dev articles covering the latest AI developments and best practices
- Technical documentation and research papers (when available)

Guidelines:
1. Provide specific, actionable recommendations
2. Consider the user's experience level and project requirements
3. Suggest appropriate tools, frameworks, and approaches
4. Identify potential challenges and solutions
5. Break down complex projects into manageable steps
6. Reference relevant concepts from your knowledge base when applicable
7. Cite sources when providing specific information (videos, articles, etc.)

Always structure your response with:
- **Project Assessment**
- **Recommended Approach**
- **Key Technologies/Tools**
- **Implementation Steps**
- **Potential Challenges**
- **Resources/Next Steps**"""

        user_prompt = f"""
User Query: {user_query}

Project Context: {project_context}

{relevant_context}

Please provide comprehensive advice for this AI project based on the knowledge from your video database and AI best practices."""

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ]
            )
            
            advice = response['message']['content']
            
            # Store conversation for context
            self.conversation_history.append({
                'user_query': user_query,
                'project_context': project_context,
                'advice': advice
            })
            
            return advice
            
        except Exception as e:
            return f"Error connecting to local LLM. Please ensure Ollama is running with model '{self.model_name}'. Error: {e}"
    
    def list_available_models(self):
        """List available Ollama models"""
        try:
            models = ollama.list()
            return [model.get('name', model.get('model', '')) for model in models.get('models', [])]
        except Exception as e:
            return []
    
    def set_model(self, model_name):
        """Switch to a different model"""
        available_models = self.list_available_models()
        if model_name in available_models:
            self.model_name = model_name
            return True
        return False
    
    def get_conversation_summary(self):
        """Get a summary of the current conversation"""
        if not self.conversation_history:
            return "No conversation history available."
        
        summary = "Conversation Summary:\n\n"
        for i, entry in enumerate(self.conversation_history, 1):
            summary += f"{i}. Query: {entry['user_query'][:100]}...\n"
            summary += f"   Context: {entry['project_context'][:100]}...\n\n"
        
        return summary


def main():
    st.set_page_config(
        page_title="Enhanced AI Project Advisor",
        page_icon="🚀",
        layout="wide"
    )
    
    # Initialize components
    if 'kb' not in st.session_state:
        with st.spinner("Loading unified knowledge base..."):
            try:
                if UNIFIED_RAG_AVAILABLE:
                    # Use the new unified RAG pipeline
                    st.session_state.kb = UnifiedRAGPipeline()
                    st.session_state.kb_type = "unified"
                    logger.info("Successfully loaded unified RAG pipeline")
                    
                    # Check if we need to migrate legacy data or integrate Daily.dev
                    stats = st.session_state.kb.get_comprehensive_stats()
                    if stats['by_source']['dailydev']['count'] == 0:
                        with st.spinner("Integrating Daily.dev articles..."):
                            try:
                                st.session_state.kb.integrate_dailydev_data()
                                logger.info("Successfully integrated Daily.dev data")
                            except Exception as e:
                                logger.warning(f"Could not integrate Daily.dev data: {e}")
                else:
                    # Fall back to simple knowledge base
                    st.session_state.kb = SimpleKnowledgeBase()
                    st.session_state.kb_type = "simple"
                    logger.info("Successfully loaded simple knowledge base")
            except Exception as e:
                st.error(f"Failed to load knowledge base: {e}")
                st.stop()
    
    if 'advisor' not in st.session_state:
        st.session_state.advisor = SimpleAIAdvisor(knowledge_base=st.session_state.kb)
    
    # Main navigation - 3 core sections as requested
    st.sidebar.title("🚀 AI Advisor System")
    
    page = st.sidebar.selectbox(
        "Choose a section:",
        [
            "🤖 AI Consultation", 
            "📚 AI Learning", 
            "📊 Project Management"
        ]
    )
    
    # Resource Statistics (always visible in sidebar)
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Knowledge Resources")
    
    # Get stats using the appropriate method based on knowledge base type
    if st.session_state.kb_type == "unified":
        stats = st.session_state.kb.get_comprehensive_stats()
    else:
        stats = st.session_state.kb.get_stats()
    
    # Display resource breakdown by source
    youtube_count = stats['by_source']['youtube']['count']
    youtube_chunks = stats['by_source']['youtube']['chunks']
    dailydev_count = stats['by_source']['dailydev']['count']
    dailydev_chunks = stats['by_source']['dailydev']['chunks']
    other_count = stats['by_source']['other']['count']
    other_chunks = stats['by_source']['other']['chunks']
    
    # YouTube Videos section
    if youtube_count > 0:
        st.sidebar.write("**📹 YouTube Videos:**")
        st.sidebar.write(f"• {youtube_count} videos")
        st.sidebar.write(f"• {youtube_chunks} chunks")
    
    # Daily.dev Articles section
    if dailydev_count > 0:
        st.sidebar.write("**📰 Daily.dev Articles:**")
        st.sidebar.write(f"• {dailydev_count} articles")
        st.sidebar.write(f"• {dailydev_chunks} chunks")
    
    # Other Resources section
    if other_count > 0:
        st.sidebar.write("**📄 Other Resources:**")
        st.sidebar.write(f"• {other_count} resources")
        st.sidebar.write(f"• {other_chunks} chunks")
    
    # Total summary
    st.sidebar.markdown("---")
    st.sidebar.write("**📈 Total Resources:**")
    st.sidebar.metric("All Resources", stats['total_resources'])
    st.sidebar.metric("Total Chunks", stats['total_chunks'])
    
    # Route to the 3 main sections
    if page == "🤖 AI Consultation":
        render_consultation_page()
    elif page == "📚 AI Learning":
        render_ai_learning_page()
    elif page == "📊 Project Management":
        render_project_management_page()


def render_consultation_page():
    """Render the main AI consultation page (original functionality)."""
    
    st.title("🤖 AI Project Advisor")
    st.markdown("Your personalized AI consultant powered by your complete video knowledge base")
    
    # Main interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💡 AI Project Consultation")
        
        # Consultation type
        consultation_type = st.selectbox(
            "What kind of help do you need?",
            [
                "General Project Advice",
                "RAG vs Fine-tuning Decision",
                "Project Scope Planning", 
                "Technology Stack Recommendation",
                "Implementation Planning",
                "Cybersecurity for AI",
                "Enterprise AI Strategy",
                "Troubleshooting",
                "Learning Path Guidance"
            ]
        )
        
        # Input based on consultation type
        if consultation_type == "General Project Advice":
            user_query = st.text_area(
                "Describe your AI project idea or question:",
                height=100,
                placeholder="I want to build a chatbot for customer service..."
            )
            project_context = st.text_input(
                "Additional context (optional):",
                placeholder="Budget constraints, timeline, team size, etc."
            )
            
        elif consultation_type == "RAG vs Fine-tuning Decision":
            user_query = st.text_area(
                "Describe your project and data:",
                height=100,
                placeholder="I have a dataset of technical documentation and want to build a Q&A system..."
            )
            
            # Specific RAG/Fine-tuning factors
            st.subheader("Project Factors")
            col_a, col_b = st.columns(2)
            with col_a:
                data_size = st.selectbox("Data Size", ["Small (<1000 docs)", "Medium (1000-10K)", "Large (10K+)"])
                update_freq = st.selectbox("Content Updates", ["Rarely", "Monthly", "Weekly", "Daily"])
            with col_b:
                accuracy_req = st.selectbox("Accuracy Requirement", ["Good enough", "High", "Critical"])
                budget = st.selectbox("Budget", ["Low", "Medium", "High"])
            
            project_context = f"Data: {data_size}, Updates: {update_freq}, Accuracy: {accuracy_req}, Budget: {budget}"
            
        elif consultation_type == "Cybersecurity for AI":
            user_query = st.text_area(
                "Describe your AI security concerns:",
                height=100,
                placeholder="How do I secure my model deployment and protect training data?"
            )
            
            security_areas = st.multiselect(
                "Security Areas of Interest:",
                ["Model Protection", "Data Privacy", "API Security", "Adversarial Attacks", "Access Control", "Compliance"]
            )
            
            project_context = f"Security focus: {', '.join(security_areas)}"
            
        elif consultation_type == "Enterprise AI Strategy":
            user_query = st.text_area(
                "Describe your organization's AI goals:",
                height=100,
                placeholder="We want to implement AI across our customer service department..."
            )
            
            org_size = st.selectbox("Organization Size", ["Startup", "Small (50-200)", "Medium (200-1000)", "Large (1000+)"])
            project_context = f"Organization: {org_size}"
            
        elif consultation_type == "Project Scope Planning":
            user_query = st.text_area(
                "Describe your project idea:",
                height=100
            )
            
            # Constraints
            st.subheader("Project Constraints")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                timeline = st.selectbox("Timeline", ["1-2 weeks", "1 month", "3 months", "6+ months", "Flexible"])
            with col_b:
                budget = st.selectbox("Budget", ["Minimal", "Low", "Medium", "High", "No constraint"])
            with col_c:
                experience = st.selectbox("Team Experience", ["Beginner", "Intermediate", "Advanced"])
            
            project_context = f"Timeline: {timeline}, Budget: {budget}, Experience: {experience}"
            
        elif consultation_type == "Technology Stack Recommendation":
            project_type = st.selectbox(
                "Project Type",
                ["Machine Learning", "Deep Learning", "NLP", "Computer Vision", "Recommender System", "Data Pipeline", "Other"]
            )
            
            requirements = st.multiselect(
                "Requirements",
                ["Real-time processing", "Scalability", "Low latency", "High accuracy", "Interpretability", "Cloud deployment", "Edge deployment"]
            )
            
            user_query = f"Technology stack for {project_type}"
            project_context = f"Requirements: {', '.join(requirements)}"
            
        elif consultation_type == "Implementation Planning":
            user_query = st.text_area(
                "Describe your project:",
                height=100
            )
            timeline = st.selectbox("Desired Timeline", ["2 weeks", "1 month", "3 months", "6 months", "Flexible"])
            project_context = f"Timeline: {timeline}"
            
        elif consultation_type == "Troubleshooting":
            user_query = st.text_area(
                "Describe the issue you're facing:",
                height=100
            )
            current_approach = st.text_area(
                "What have you tried so far?",
                height=80
            )
            project_context = current_approach
            
        else:  # Learning Path Guidance
            goal = st.text_input("What do you want to learn/achieve?")
            current_level = st.selectbox("Current Level", ["Complete Beginner", "Some Programming", "Some ML", "Intermediate", "Advanced"])
            user_query = f"Learning path for: {goal}"
            project_context = f"Current level: {current_level}"
        
        # Generate advice button
        if st.button("🧠 Get AI Advice", type="primary"):
            if user_query.strip():
                with st.spinner("Analyzing your query and searching knowledge base..."):
                    try:
                        advice = st.session_state.advisor.generate_advice(user_query, project_context)
                        
                        st.subheader("🎯 AI Project Advice")
                        st.markdown(advice)
                        
                        # Show relevant sources
                        with st.expander("📚 Knowledge Sources Used"):
                            relevant_knowledge = st.session_state.kb.search_knowledge(user_query, 3)
                            for i, result in enumerate(relevant_knowledge, 1):
                                metadata = result['metadata']
                                st.write(f"**{i}. {metadata['title']}** by {metadata['uploader']}")
                                st.write(f"🔗 [Watch Video]({metadata['url']})")
                                st.write("---")
                        
                    except Exception as e:
                        st.error(f"Error generating advice: {e}")
                        st.info("Make sure Ollama is running locally with a supported model.")
            else:
                st.warning("Please enter your query first.")
    
    with col2:
        st.header("⚙️ Settings")
        
        # Model selection
        available_models = st.session_state.advisor.list_available_models()
        if available_models:
            current_model = st.selectbox(
                "Select LLM Model:",
                available_models,
                index=available_models.index(st.session_state.advisor.model_name) if st.session_state.advisor.model_name in available_models else 0
            )
            
            if current_model != st.session_state.advisor.model_name:
                st.session_state.advisor.set_model(current_model)
                st.success(f"Switched to {current_model}")
        else:
            st.warning("No Ollama models found. Please install Ollama and download a model.")
            st.markdown("```bash\n# Install a model\nollama pull llama2\n```")
        
        # Quick actions
        st.subheader("🔧 Quick Actions")
        
        if st.button("📊 Knowledge Base Stats"):
            stats = st.session_state.kb.get_stats()
            st.json({
                'total_resources': stats['total_resources'],
                'total_chunks': stats['total_chunks'],
                'by_type': stats['by_type'],
                'daily_dev_articles': stats.get('daily_dev_count', 0)
            })
        
        if st.button("💬 Conversation Summary"):
            summary = st.session_state.advisor.get_conversation_summary()
            st.text_area("Summary:", summary, height=200)
        
        # Export options
        st.subheader("📥 Export")
        if st.button("Export Conversation"):
            conversation = st.session_state.advisor.conversation_history
            st.download_button(
                "Download JSON",
                json.dumps(conversation, indent=2),
                "conversation_history.json",
                "application/json"
            )


def render_knowledge_explorer():
    """Render knowledge base exploration interface."""
    
    st.header("💡 Knowledge Base Explorer")
    st.write("Search and explore your AI knowledge base of 80 educational videos")
    
    # Search interface
    search_query = st.text_input("🔍 Search Knowledge Base:", placeholder="Enter keywords like 'RAG', 'neural networks', 'cybersecurity'...")
    
    if search_query:
        results = st.session_state.kb.search_knowledge(search_query, 10)
        
        if results:
            st.subheader(f"📚 Found {len(results)} relevant sources")
            
            for i, result in enumerate(results, 1):
                with st.expander(f"{i}. {result['metadata']['title']}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write("**Content:**")
                        st.write(result['content'][:500] + "..." if len(result['content']) > 500 else result['content'])
                        
                    with col2:
                        # Handle different source types
                        metadata = result['metadata']
                        source_type = metadata.get('source_type', 'unknown')
                        
                        if source_type == 'video':
                            st.write(f"**Uploader:** {metadata.get('uploader', 'Unknown')}")
                            st.write(f"**Relevance:** {(1-result['distance'])*100:.1f}%")
                            st.markdown(f"🔗 [Watch Video]({metadata['url']})")
                        else:
                            # Daily.dev article or other content
                            author = metadata.get('author', metadata.get('original_source', 'Daily.dev'))
                            st.write(f"**Source:** {author}")
                            st.write(f"**Relevance:** {(1-result['distance'])*100:.1f}%")
                            if 'source_url' in metadata:
                                st.markdown(f"🔗 [Read Article]({metadata['source_url']})")
                            else:
                                st.markdown(f"🔗 [View Content]({metadata.get('url', '#')})")
        else:
            st.info("No results found. Try different keywords.")
    
    # Knowledge base overview
    st.subheader("📊 Knowledge Base Overview")
    
    stats = st.session_state.kb.get_stats()
    
    if st.session_state.kb_type == "unified":
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Resources", stats['total_resources'])
        with col2:
            st.metric("Knowledge Chunks", stats['total_chunks'])
        with col3:
            resource_types = len(stats.get('by_type', {}))
            st.metric("Resource Types", resource_types)
        
        # Show resource breakdown
        if stats.get('by_type'):
            st.subheader("📁 Resource Breakdown")
            for rtype, count in stats['by_type'].items():
                st.write(f"**{rtype.upper()}**: {count} resources")
    else:
        # Legacy display
        col1, col2, col3 = st.columns(3)
        with col1:
            unique_videos = stats.get('unique_videos', stats.get('total_resources', 0))
            st.metric("Total Videos", unique_videos)
        with col2:
            st.metric("Knowledge Chunks", stats['total_chunks'])
        with col3:
            st.metric("Coverage", "100%")
        
        # Sample topics for legacy mode
        if stats.get('topics'):
            st.subheader("📹 Available Topics")
            
            # Show topics in a grid
            topics_per_row = 3
            for i in range(0, min(12, len(stats['topics'])), topics_per_row):
                cols = st.columns(topics_per_row)
                for j, col in enumerate(cols):
                    if i + j < len(stats['topics']):
                        topic = stats['topics'][i + j]
                        with col:
                            st.write(f"• {topic[:60]}{'...' if len(topic) > 60 else ''}")


def render_ai_learning_page():
    """Render the AI Learning section."""
    st.title("📚 AI Learning System")
    st.markdown("Personalized learning paths and skill development based on your knowledge base")
    
    # Learning dashboard
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🎯 Learning Paths")
        
        # Learning path selection
        learning_path = st.selectbox(
            "Choose your learning focus:",
            [
                "Complete AI Beginner",
                "Machine Learning Fundamentals", 
                "Deep Learning & Neural Networks",
                "Natural Language Processing",
                "Computer Vision",
                "RAG Systems & Vector Databases",
                "AI Security & Ethics",
                "MLOps & Production AI",
                "Custom Learning Path"
            ]
        )
        
        if learning_path == "Custom Learning Path":
            custom_topics = st.text_area(
                "What specific topics do you want to learn?",
                placeholder="Enter topics like: transformers, BERT, fine-tuning, etc."
            )
            if custom_topics:
                learning_path = f"Custom: {custom_topics}"
        
        # Current skill level
        skill_level = st.selectbox(
            "Your current skill level:",
            ["Complete Beginner", "Some Programming", "Some ML Experience", "Intermediate", "Advanced"]
        )
        
        # Generate learning path
        if st.button("🚀 Generate Learning Path", type="primary"):
            with st.spinner("Creating personalized learning path..."):
                # Search for relevant content
                search_query = learning_path.replace("Custom: ", "")
                relevant_content = st.session_state.kb.search_knowledge(search_query, 10)
                
                st.subheader("📋 Your Personalized Learning Path")
                
                if relevant_content:
                    st.success(f"Found {len(relevant_content)} relevant resources for your learning path!")
                    
                    # Group by source type
                    videos = [r for r in relevant_content if r['metadata'].get('source_type') == 'video']
                    articles = [r for r in relevant_content if r['metadata'].get('source_type') != 'video']
                    
                    # Display learning sequence
                    st.markdown("### 🎬 Video Learning Sequence")
                    for i, video in enumerate(videos[:5], 1):
                        with st.expander(f"Step {i}: {video['metadata']['title']}"):
                            st.write(f"**Instructor:** {video['metadata']['uploader']}")
                            st.write(f"**Relevance:** {(1-video['distance'])*100:.1f}%")
                            st.write("**Key Topics:**")
                            st.write(video['content'][:300] + "...")
                            st.markdown(f"🔗 [Watch Video]({video['metadata']['url']})")
                    
                    if articles:
                        st.markdown("### 📰 Supplementary Reading")
                        for i, article in enumerate(articles[:3], 1):
                            with st.expander(f"Article {i}: {article['metadata']['title']}"):
                                st.write(f"**Source:** {article['metadata']['uploader']}")
                                st.write(f"**Relevance:** {(1-article['distance'])*100:.1f}%")
                                st.write(article['content'][:300] + "...")
                                if 'url' in article['metadata']:
                                    st.markdown(f"🔗 [Read Article]({article['metadata']['url']})")
                else:
                    st.warning("No specific resources found for this learning path. Try a different topic or check the knowledge base.")
    
    with col2:
        st.header("📊 Learning Progress")
        
        # Mock progress tracking (would be enhanced with real tracking)
        st.subheader("🏆 Your Stats")
        st.metric("Videos Watched", "12/80")
        st.metric("Articles Read", "8/25") 
        st.metric("Learning Streak", "5 days")
        
        # Skill assessment
        st.subheader("🧠 Quick Assessment")
        if st.button("Take Skill Quiz"):
            st.info("Skill assessment feature coming soon!")
        
        # Recommended next steps
        st.subheader("🎯 Recommended Next")
        st.write("Based on your learning path:")
        st.write("• Complete 'Neural Networks Basics'")
        st.write("• Read 'Transformer Architecture'")
        st.write("• Practice with code examples")
        
        # Learning resources
        st.subheader("📚 Quick Resources")
        stats = st.session_state.kb.get_stats()
        st.write(f"📹 {stats['by_source']['youtube']['count']} Video Tutorials")
        st.write(f"📰 {stats['by_source']['dailydev']['count']} Articles")
        st.write(f"📊 {stats['total_chunks']} Knowledge Chunks")


def render_project_management_page():
    """Render the Project Management section."""
    st.title("📊 AI Project Management")
    st.markdown("Track and manage your AI projects with intelligent insights")
    
    # Initialize project data in session state
    if 'projects' not in st.session_state:
        st.session_state.projects = []
    
    # Main project management interface
    tab1, tab2, tab3 = st.tabs(["📋 Active Projects", "➕ New Project", "📈 Analytics"])
    
    with tab1:
        st.header("Current Projects")
        
        if st.session_state.projects:
            for i, project in enumerate(st.session_state.projects):
                with st.expander(f"🚀 {project['name']} - {project['status']}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Description:** {project['description']}")
                        st.write(f"**Timeline:** {project['timeline']}")
                        st.write(f"**Technology:** {project['tech_stack']}")
                        
                        # Progress bar
                        progress = project.get('progress', 0)
                        st.progress(progress / 100)
                        st.write(f"Progress: {progress}%")
                        
                        # Recent activity
                        if project.get('activities'):
                            st.write("**Recent Activity:**")
                            for activity in project['activities'][-3:]:
                                st.write(f"• {activity}")
                    
                    with col2:
                        st.write(f"**Status:** {project['status']}")
                        st.write(f"**Priority:** {project['priority']}")
                        st.write(f"**Created:** {project['created_date']}")
                        
                        # Action buttons
                        if st.button(f"Update Progress", key=f"update_{i}"):
                            new_progress = st.slider("Progress %", 0, 100, progress, key=f"progress_{i}")
                            st.session_state.projects[i]['progress'] = new_progress
                            st.success("Progress updated!")
                        
                        if st.button(f"Get AI Advice", key=f"advice_{i}"):
                            # Generate project-specific advice
                            query = f"Help with {project['name']}: {project['description']}"
                            with st.spinner("Getting AI advice..."):
                                advice = st.session_state.advisor.generate_advice(
                                    query, 
                                    f"Tech stack: {project['tech_stack']}, Timeline: {project['timeline']}"
                                )
                                st.markdown("**AI Recommendation:**")
                                st.write(advice[:500] + "..." if len(advice) > 500 else advice)
        else:
            st.info("No active projects. Create your first project in the 'New Project' tab!")
    
    with tab2:
        st.header("Create New Project")
        
        with st.form("new_project_form"):
            project_name = st.text_input("Project Name", placeholder="My AI Chatbot")
            project_description = st.text_area(
                "Project Description", 
                placeholder="A customer service chatbot using RAG architecture..."
            )
            
            col1, col2 = st.columns(2)
            with col1:
                project_type = st.selectbox(
                    "Project Type",
                    ["Machine Learning", "Deep Learning", "NLP", "Computer Vision", 
                     "Data Pipeline", "RAG System", "Other"]
                )
                timeline = st.selectbox(
                    "Timeline", 
                    ["1-2 weeks", "1 month", "3 months", "6+ months"]
                )
            
            with col2:
                priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
                tech_stack = st.text_input(
                    "Technology Stack", 
                    placeholder="Python, LangChain, ChromaDB, FastAPI"
                )
            
            # Project goals
            goals = st.text_area(
                "Project Goals & Success Metrics",
                placeholder="Achieve 90% accuracy, handle 1000 queries/day, etc."
            )
            
            submitted = st.form_submit_button("🚀 Create Project", type="primary")
            
            if submitted and project_name and project_description:
                new_project = {
                    'name': project_name,
                    'description': project_description,
                    'type': project_type,
                    'timeline': timeline,
                    'priority': priority,
                    'tech_stack': tech_stack,
                    'goals': goals,
                    'status': 'Planning',
                    'progress': 0,
                    'created_date': datetime.now().strftime("%Y-%m-%d"),
                    'activities': [f"Project created on {datetime.now().strftime('%Y-%m-%d')}"]
                }
                
                st.session_state.projects.append(new_project)
                st.success(f"Project '{project_name}' created successfully!")
                
                # Generate initial AI advice
                with st.spinner("Generating initial project advice..."):
                    advice = st.session_state.advisor.generate_advice(
                        f"New project: {project_description}",
                        f"Type: {project_type}, Timeline: {timeline}, Tech: {tech_stack}"
                    )
                    
                    st.subheader("🤖 Initial AI Recommendations")
                    st.markdown(advice)
    
    with tab3:
        st.header("Project Analytics")
        
        if st.session_state.projects:
            # Project statistics
            total_projects = len(st.session_state.projects)
            completed_projects = len([p for p in st.session_state.projects if p['status'] == 'Completed'])
            in_progress = len([p for p in st.session_state.projects if p['status'] in ['In Progress', 'Planning']])
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Projects", total_projects)
            with col2:
                st.metric("Completed", completed_projects)
            with col3:
                st.metric("In Progress", in_progress)
            with col4:
                avg_progress = sum(p.get('progress', 0) for p in st.session_state.projects) / total_projects
                st.metric("Avg Progress", f"{avg_progress:.1f}%")
            
            # Project breakdown by type
            st.subheader("📊 Projects by Type")
            project_types = {}
            for project in st.session_state.projects:
                ptype = project['type']
                project_types[ptype] = project_types.get(ptype, 0) + 1
            
            for ptype, count in project_types.items():
                st.write(f"**{ptype}:** {count} projects")
            
            # Recent activity
            st.subheader("📈 Recent Activity")
            all_activities = []
            for project in st.session_state.projects:
                for activity in project.get('activities', []):
                    all_activities.append(f"{project['name']}: {activity}")
            
            for activity in all_activities[-5:]:
                st.write(f"• {activity}")
        else:
            st.info("No projects to analyze. Create some projects first!")


if __name__ == "__main__":
    main()