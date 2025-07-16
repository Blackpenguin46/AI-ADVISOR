#!/usr/bin/env python3

import streamlit as st
import json
import ollama
from pathlib import Path

# Simple knowledge base class that uses JSON instead of ChromaDB
class SimpleKnowledgeBase:
    def __init__(self):
        self.knowledge_db = self.load_knowledge_base()
    
    def load_knowledge_base(self):
        """Load the complete knowledge base"""
        kb_file = "knowledge_base_final.json"
        if Path(kb_file).exists():
            with open(kb_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def search_knowledge(self, query, n_results=5):
        """Search knowledge base and return in ChromaDB format"""
        query_words = query.lower().split()
        results = []
        
        for url, video_data in self.knowledge_db.items():
            title = video_data['title'].lower()
            transcript = video_data.get('transcript', '').lower()
            
            # Score based on keyword matches
            score = 0
            for word in query_words:
                score += title.count(word) * 3
                score += transcript.count(word)
            
            if score > 0:
                # Get relevant chunk
                chunks = video_data.get('chunks', [])
                if chunks:
                    # Find best matching chunk
                    best_chunk = chunks[0]
                    for chunk in chunks[:3]:
                        chunk_lower = chunk.lower()
                        if any(word in chunk_lower for word in query_words):
                            best_chunk = chunk
                            break
                else:
                    best_chunk = video_data.get('transcript', '')[:500]
                
                results.append({
                    'content': best_chunk,
                    'metadata': {
                        'title': video_data['title'],
                        'url': url,
                        'uploader': video_data.get('uploader', 'Unknown')
                    },
                    'distance': 1.0 - (score / 100)  # Convert score to distance
                })
        
        # Sort by score (lower distance = better match)
        results.sort(key=lambda x: x['distance'])
        return results[:n_results]
    
    def get_stats(self):
        """Get knowledge base statistics"""
        total_chunks = sum(v.get('chunk_count', 0) for v in self.knowledge_db.values())
        unique_videos = len(self.knowledge_db)
        topics = [v['title'] for v in self.knowledge_db.values()]
        
        return {
            'total_chunks': total_chunks,
            'unique_videos': unique_videos,
            'topics': topics
        }

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
            
            context += f"[Source {i}: {metadata['title']} by {metadata['uploader']}]\n"
            context += f"{content}\n\n"
        
        return context
    
    def generate_advice(self, user_query, project_context=""):
        """Generate AI project advice using local LLM and knowledge base"""
        
        # Search for relevant knowledge
        relevant_context = self.search_relevant_knowledge(user_query)
        
        # Build the prompt
        system_prompt = """You are an expert AI project advisor with comprehensive knowledge from 80 educational videos covering AI concepts, frameworks, and implementation strategies.

Guidelines:
1. Provide specific, actionable recommendations
2. Consider the user's experience level and project requirements
3. Suggest appropriate tools, frameworks, and approaches
4. Identify potential challenges and solutions
5. Break down complex projects into manageable steps
6. Reference relevant concepts from your knowledge base when applicable

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
        page_title="AI Project Advisor",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 AI Project Advisor")
    st.markdown("Your personalized AI consultant powered by your complete video knowledge base")
    
    # Initialize components using the complete knowledge base
    if 'kb' not in st.session_state:
        with st.spinner("Loading complete knowledge base (80 videos)..."):
            st.session_state.kb = SimpleKnowledgeBase()
    
    if 'advisor' not in st.session_state:
        st.session_state.advisor = SimpleAIAdvisor(knowledge_base=st.session_state.kb)
    
    # Sidebar for knowledge base management
    st.sidebar.header("📚 Knowledge Base")
    
    # Display knowledge base stats
    stats = st.session_state.kb.get_stats()
    st.sidebar.metric("Total Video Chunks", stats['total_chunks'])
    st.sidebar.metric("Unique Videos", stats['unique_videos'])
    st.sidebar.success("✅ Complete Database Loaded")
    
    if stats['topics']:
        with st.sidebar.expander("📹 Available Videos"):
            for topic in stats['topics'][:10]:  # Show first 10
                st.write(f"• {topic[:50]}...")
    
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
                'total_videos': stats['unique_videos'],
                'total_chunks': stats['total_chunks'],
                'coverage': '100%'
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

if __name__ == "__main__":
    main()