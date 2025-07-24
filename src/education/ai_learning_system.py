"""
AI Learning System - Generate personalized AI lessons based on user prompts.
"""

import streamlit as st
from typing import Dict, List, Any, Optional


class AILearningSystem:
    """Generate AI learning content based on user prompts and context."""
    
    def __init__(self, advisor):
        self.advisor = advisor  # Use the same advisor instance for consistency
        self.learning_history = []
    
    def generate_lesson(self, topic_area: str, user_prompt: str, learning_context: str = "") -> str:
        """Generate a personalized AI lesson based on user input."""
        
        # Create learning-focused system prompt
        system_prompt = f"""You are an expert AI educator with comprehensive knowledge from 80 educational videos covering all aspects of artificial intelligence.

Your role is to create personalized learning lessons that are:
1. **Educational and comprehensive** - Cover concepts thoroughly
2. **Practical and actionable** - Include real-world applications
3. **Beginner-friendly** - Explain complex concepts clearly
4. **Example-rich** - Provide concrete examples and use cases
5. **Step-by-step** - Break down complex topics into digestible parts

For the topic area "{topic_area}", structure your lesson with:
- **📚 Concept Overview** - What it is and why it matters
- **🔧 How It Works** - Technical explanation in simple terms
- **💡 Real-World Examples** - Practical applications and use cases
- **🛠️ Implementation Basics** - Getting started steps
- **⚠️ Common Pitfalls** - What to avoid
- **📈 Next Steps** - How to advance your knowledge

Make the lesson engaging, informative, and tailored to the user's specific interests."""

        # Build the learning prompt
        learning_prompt = f"""
Topic Area: {topic_area}
Learning Request: {user_prompt}
Learning Context: {learning_context}

Please create a comprehensive AI lesson based on my request. Focus on teaching me the concepts, providing examples, and giving practical guidance I can use.

Use information from your AI knowledge base to make the lesson as informative and accurate as possible."""

        try:
            response = self.advisor.advisor.generate_advice(learning_prompt, f"Learning Context: {learning_context}")
            
            # Store learning session
            self.learning_history.append({
                'topic_area': topic_area,
                'user_prompt': user_prompt,
                'learning_context': learning_context,
                'lesson': response
            })
            
            return response
            
        except Exception as e:
            return f"Error generating lesson: {e}"
    
    def get_learning_history(self):
        """Get user's learning history."""
        return self.learning_history


def create_ai_learning_dashboard(advisor):
    """Create the AI Learning dashboard."""
    
    if 'learning_system' not in st.session_state:
        st.session_state.learning_system = AILearningSystem(advisor)
    
    st.header("📚 AI Learning System")
    st.write("Get personalized AI lessons tailored to your specific questions and learning goals")
    
    # Main learning interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎯 Request Your AI Lesson")
        
        # Topic area selection
        topic_area = st.selectbox(
            "Choose your AI learning area:",
            [
                "Machine Learning Fundamentals",
                "Deep Learning & Neural Networks", 
                "Natural Language Processing (NLP)",
                "RAG (Retrieval Augmented Generation)",
                "Fine-tuning & Model Training",
                "Computer Vision & Image Processing",
                "Large Language Models (LLMs)",
                "AI Ethics & Responsible AI",
                "Model Deployment & MLOps",
                "Vector Databases & Embeddings",
                "Transformers & Attention Mechanisms",
                "Generative AI & Diffusion Models",
                "Reinforcement Learning",
                "AI for Business & Strategy",
                "Custom Topic"
            ]
        )
        
        # Learning prompt based on topic area
        if topic_area == "Machine Learning Fundamentals":
            user_prompt = st.text_area(
                "What specific ML concept would you like to learn?",
                height=100,
                placeholder="Explain supervised vs unsupervised learning with examples, or How do I choose the right ML algorithm for my problem?"
            )
            
            # Additional context options
            st.subheader("📋 Learning Context")
            col_a, col_b = st.columns(2)
            with col_a:
                experience = st.selectbox("Your ML Experience", ["Complete Beginner", "Some Programming", "Basic ML Knowledge", "Intermediate", "Advanced"])
                focus = st.selectbox("Learning Focus", ["Conceptual Understanding", "Practical Implementation", "Both Theory and Practice"])
            with col_b:
                goal = st.selectbox("Learning Goal", ["General Knowledge", "Specific Project", "Career Development", "Academic Study"])
                depth = st.selectbox("Lesson Depth", ["Quick Overview", "Detailed Explanation", "Comprehensive Deep-dive"])
            
            learning_context = f"Experience: {experience}, Focus: {focus}, Goal: {goal}, Depth: {depth}"
            
        elif topic_area == "RAG (Retrieval Augmented Generation)":
            user_prompt = st.text_area(
                "What about RAG would you like to learn?",
                height=100,
                placeholder="How does RAG work step-by-step? or When should I use RAG vs fine-tuning? or How to build a RAG system for my documents?"
            )
            
            st.subheader("📋 RAG Learning Context")
            col_a, col_b = st.columns(2)
            with col_a:
                rag_experience = st.selectbox("RAG Experience", ["Never heard of it", "Know the concept", "Built simple RAG", "Advanced RAG user"])
                use_case = st.selectbox("Intended Use Case", ["General Learning", "Document Q&A", "Customer Support", "Research Assistant", "Code Assistant"])
            with col_b:
                technical_level = st.selectbox("Technical Detail", ["High-level concepts only", "Some technical details", "Full implementation details"])
                timeframe = st.selectbox("Implementation Timeline", ["Just learning", "Next week", "Next month", "Future project"])
            
            learning_context = f"RAG Experience: {rag_experience}, Use Case: {use_case}, Technical Level: {technical_level}, Timeline: {timeframe}"
            
        elif topic_area == "Deep Learning & Neural Networks":
            user_prompt = st.text_area(
                "What neural network concept would you like to explore?",
                height=100,
                placeholder="How do neural networks actually learn? or Explain backpropagation in simple terms, or What's the difference between CNN, RNN, and Transformers?"
            )
            
            st.subheader("📋 Deep Learning Context")
            col_a, col_b = st.columns(2)
            with col_a:
                math_comfort = st.selectbox("Math Comfort Level", ["Avoid heavy math", "Basic math OK", "Comfortable with math", "Advanced math welcome"])
                application = st.selectbox("Application Interest", ["General Understanding", "Computer Vision", "NLP/Text", "Time Series", "Generative AI"])
            with col_b:
                framework = st.selectbox("Preferred Framework", ["No preference", "PyTorch", "TensorFlow", "Keras", "JAX"])
                learning_style = st.selectbox("Learning Style", ["Conceptual first", "Code-heavy", "Balanced theory/practice"])
            
            learning_context = f"Math Level: {math_comfort}, Application: {application}, Framework: {framework}, Style: {learning_style}"
            
        elif topic_area == "Natural Language Processing (NLP)":
            user_prompt = st.text_area(
                "What NLP topic interests you?",
                height=100,
                placeholder="How does text preprocessing work? or Explain word embeddings and their uses, or How to build a sentiment analysis system?"
            )
            
            st.subheader("📋 NLP Learning Context")
            col_a, col_b = st.columns(2)
            with col_a:
                nlp_level = st.selectbox("NLP Experience", ["Beginner", "Some text processing", "Basic NLP", "Intermediate", "Advanced"])
                interest = st.selectbox("Primary Interest", ["Text Classification", "Text Generation", "Information Extraction", "Chatbots", "Language Understanding"])
            with col_b:
                tools = st.selectbox("Tool Preference", ["No preference", "spaCy", "NLTK", "Hugging Face", "OpenAI API"])
                project_type = st.selectbox("Project Type", ["Learning exercise", "Personal project", "Work project", "Research"])
            
            learning_context = f"Experience: {nlp_level}, Interest: {interest}, Tools: {tools}, Project: {project_type}"
            
        elif topic_area == "Large Language Models (LLMs)":
            user_prompt = st.text_area(
                "What about LLMs would you like to understand?",
                height=100,
                placeholder="How do LLMs like GPT work internally? or How to use LLMs effectively in applications? or What are the limitations of current LLMs?"
            )
            
            st.subheader("📋 LLM Learning Context")
            col_a, col_b = st.columns(2)
            with col_a:
                llm_usage = st.selectbox("LLM Experience", ["Never used", "Basic prompting", "API integration", "Advanced techniques"])
                focus_area = st.selectbox("Focus Area", ["How they work", "Practical usage", "Integration techniques", "Latest developments"])
            with col_b:
                application_goal = st.selectbox("Application Goal", ["General understanding", "Build applications", "Improve prompting", "Business integration"])
                technical_depth = st.selectbox("Technical Depth", ["High-level overview", "Moderate detail", "Deep technical"])
            
            learning_context = f"Usage: {llm_usage}, Focus: {focus_area}, Goal: {application_goal}, Depth: {technical_depth}"
            
        elif topic_area == "Model Deployment & MLOps":
            user_prompt = st.text_area(
                "What deployment or MLOps topic would you like to learn?",
                height=100,
                placeholder="How to deploy ML models to production? or What is MLOps and why do I need it? or How to monitor model performance in production?"
            )
            
            st.subheader("📋 Deployment Context")
            col_a, col_b = st.columns(2)
            with col_a:
                deployment_exp = st.selectbox("Deployment Experience", ["Never deployed", "Local deployment", "Basic cloud", "Production experience"])
                infrastructure = st.selectbox("Infrastructure Preference", ["Local/On-premise", "AWS", "Google Cloud", "Azure", "Any cloud"])
            with col_b:
                model_type = st.selectbox("Model Type", ["Traditional ML", "Deep Learning", "LLM/Generative", "Computer Vision"])
                scale = st.selectbox("Expected Scale", ["Personal project", "Small business", "Enterprise", "High-traffic"])
            
            learning_context = f"Experience: {deployment_exp}, Infrastructure: {infrastructure}, Model: {model_type}, Scale: {scale}"
            
        elif topic_area == "AI Ethics & Responsible AI":
            user_prompt = st.text_area(
                "What AI ethics topic concerns you?",
                height=100,
                placeholder="How to ensure AI fairness and avoid bias? or What are the privacy implications of AI? or How to build trustworthy AI systems?"
            )
            
            st.subheader("📋 Ethics Context")
            col_a, col_b = st.columns(2)
            with col_a:
                role = st.selectbox("Your Role", ["Developer/Engineer", "Data Scientist", "Product Manager", "Business Leader", "Researcher", "Student"])
                industry = st.selectbox("Industry", ["Technology", "Healthcare", "Finance", "Education", "Government", "Other/General"])
            with col_b:
                concern_level = st.selectbox("Concern Level", ["General awareness", "Specific project needs", "Compliance requirements", "Deep ethical study"])
                focus = st.selectbox("Primary Focus", ["Bias and Fairness", "Privacy and Security", "Transparency", "Accountability", "All aspects"])
            
            learning_context = f"Role: {role}, Industry: {industry}, Concern: {concern_level}, Focus: {focus}"
            
        else:  # Custom Topic or other areas
            user_prompt = st.text_area(
                f"What would you like to learn about {topic_area}?",
                height=100,
                placeholder="Enter your specific question or learning request..."
            )
            
            # General learning context
            col_a, col_b = st.columns(2)
            with col_a:
                experience_level = st.selectbox("Experience Level", ["Beginner", "Intermediate", "Advanced"])
                learning_goal = st.selectbox("Learning Goal", ["Understand concepts", "Practical implementation", "Career development", "Project application"])
            with col_b:
                preferred_depth = st.selectbox("Preferred Depth", ["Quick overview", "Detailed explanation", "Comprehensive coverage"])
                include_examples = st.checkbox("Include practical examples", value=True)
            
            learning_context = f"Level: {experience_level}, Goal: {learning_goal}, Depth: {preferred_depth}, Examples: {include_examples}"
        
        # Generate lesson button
        if st.button("📖 Generate AI Lesson", type="primary"):
            if user_prompt.strip():
                with st.spinner("Creating your personalized AI lesson..."):
                    try:
                        lesson = st.session_state.learning_system.generate_lesson(
                            topic_area, user_prompt, learning_context
                        )
                        
                        st.subheader("📚 Your AI Lesson")
                        st.markdown(lesson)
                        
                        # Show knowledge sources
                        with st.expander("📖 Knowledge Sources Referenced"):
                            relevant_knowledge = st.session_state.kb.search_knowledge(user_prompt, 3)
                            for i, result in enumerate(relevant_knowledge, 1):
                                metadata = result['metadata']
                                st.write(f"**{i}. {metadata['title']}** by {metadata['uploader']}")
                                st.write(f"🔗 [Watch Video]({metadata['url']})")
                                st.write("---")
                        
                        # Quick follow-up questions
                        st.subheader("🤔 Follow-up Questions")
                        follow_up_suggestions = [
                            "Can you give me a practical example?",
                            "What are the main challenges with this approach?",
                            "How does this compare to alternatives?",
                            "What tools or libraries should I use?",
                            "What should I learn next?"
                        ]
                        
                        for suggestion in follow_up_suggestions:
                            if st.button(suggestion, key=f"followup_{suggestion}"):
                                follow_up_lesson = st.session_state.learning_system.generate_lesson(
                                    topic_area, suggestion, f"Previous topic: {user_prompt}"
                                )
                                st.markdown("---")
                                st.markdown(follow_up_lesson)
                        
                    except Exception as e:
                        st.error(f"Error generating lesson: {e}")
                        st.info("Make sure Ollama is running locally with a supported model.")
            else:
                st.warning("Please enter your learning request first.")
    
    with col2:
        st.subheader("📊 Learning Dashboard")
        
        # Learning progress
        learning_history = st.session_state.learning_system.get_learning_history()
        
        if learning_history:
            st.metric("Lessons Completed", len(learning_history))
            
            # Recent topics
            st.write("**Recent Learning Topics:**")
            for session in learning_history[-5:]:  # Show last 5
                st.write(f"• {session['topic_area']}")
            
            # Export learning history
            if st.button("📥 Export Learning History"):
                import json
                st.download_button(
                    "Download Learning History",
                    json.dumps(learning_history, indent=2),
                    "ai_learning_history.json",
                    "application/json"
                )
        else:
            st.info("Start learning to see your progress here!")
        
        # Quick topic suggestions
        st.subheader("💡 Quick Learning Ideas")
        quick_topics = [
            "What is the difference between AI, ML, and DL?",
            "How do I get started with RAG?",
            "Explain transformers in simple terms",
            "When should I use fine-tuning?",
            "How do embeddings work?",
            "What makes a good AI dataset?",
            "How to evaluate model performance?",
            "AI safety and alignment basics"
        ]
        
        for topic in quick_topics[:4]:  # Show first 4
            if st.button(topic, key=f"quick_{topic}"):
                # Auto-fill the prompt
                st.session_state.quick_topic = topic