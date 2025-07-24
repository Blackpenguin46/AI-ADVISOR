"""
AI Project Management and Tracking System.
Helps users plan, track, and manage AI projects from conception to deployment.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import json


class ProjectStatus(Enum):
    PLANNING = "Planning"
    IN_PROGRESS = "In Progress"
    TESTING = "Testing"
    DEPLOYED = "Deployed"
    ON_HOLD = "On Hold"
    COMPLETED = "Completed"


class TaskStatus(Enum):
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    REVIEW = "Review"
    DONE = "Done"
    BLOCKED = "Blocked"


class Priority(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


@dataclass
class Milestone:
    """Represents a project milestone."""
    id: str
    title: str
    description: str
    due_date: str
    status: TaskStatus
    completion_percentage: int = 0


@dataclass
class Task:
    """Represents a project task."""
    id: str
    title: str
    description: str
    assignee: str
    status: TaskStatus
    priority: Priority
    estimated_hours: int
    actual_hours: int = 0
    due_date: Optional[str] = None
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class AIProject:
    """Represents an AI project with all its components."""
    id: str
    name: str
    description: str
    project_type: str  # "RAG", "Fine-tuning", "Computer Vision", etc.
    status: ProjectStatus
    start_date: str
    end_date: Optional[str]
    team_members: List[str]
    milestones: List[Milestone]
    tasks: List[Task]
    tech_stack: List[str]
    budget: Optional[float] = None
    risks: List[str] = None
    
    def __post_init__(self):
        if self.risks is None:
            self.risks = []


class AIProjectTemplate:
    """Templates for different types of AI projects."""
    
    @staticmethod
    def create_rag_project_template(project_name: str) -> AIProject:
        """Create a template for a RAG project."""
        
        milestones = [
            Milestone("m1", "Data Collection Complete", "Gather and organize source documents", 
                     (datetime.now() + timedelta(weeks=2)).strftime("%Y-%m-%d"), TaskStatus.TODO),
            Milestone("m2", "Vector Database Setup", "Implement and populate vector database", 
                     (datetime.now() + timedelta(weeks=4)).strftime("%Y-%m-%d"), TaskStatus.TODO),
            Milestone("m3", "RAG System MVP", "Basic RAG system functional", 
                     (datetime.now() + timedelta(weeks=6)).strftime("%Y-%m-%d"), TaskStatus.TODO),
            Milestone("m4", "Testing Complete", "System tested and optimized", 
                     (datetime.now() + timedelta(weeks=8)).strftime("%Y-%m-%d"), TaskStatus.TODO),
            Milestone("m5", "Production Deployment", "System live in production", 
                     (datetime.now() + timedelta(weeks=10)).strftime("%Y-%m-%d"), TaskStatus.TODO)
        ]
        
        tasks = [
            Task("t1", "Document Collection", "Gather all source documents and data", 
                 "Data Team", TaskStatus.TODO, Priority.HIGH, 20),
            Task("t2", "Data Preprocessing", "Clean and format documents for ingestion", 
                 "Data Team", TaskStatus.TODO, Priority.HIGH, 30, dependencies=["t1"]),
            Task("t3", "Choose Embedding Model", "Research and select appropriate embedding model", 
                 "ML Team", TaskStatus.TODO, Priority.MEDIUM, 16),
            Task("t4", "Vector Database Setup", "Set up and configure vector database", 
                 "Infrastructure Team", TaskStatus.TODO, Priority.HIGH, 24),
            Task("t5", "Document Chunking Strategy", "Implement optimal text chunking", 
                 "ML Team", TaskStatus.TODO, Priority.MEDIUM, 20, dependencies=["t2"]),
            Task("t6", "RAG Pipeline Implementation", "Build core RAG functionality", 
                 "Development Team", TaskStatus.TODO, Priority.CRITICAL, 40, dependencies=["t3", "t4", "t5"]),
            Task("t7", "Query Processing", "Implement query understanding and routing", 
                 "Development Team", TaskStatus.TODO, Priority.HIGH, 24, dependencies=["t6"]),
            Task("t8", "Response Generation", "Implement LLM integration for responses", 
                 "Development Team", TaskStatus.TODO, Priority.HIGH, 32, dependencies=["t6"]),
            Task("t9", "Evaluation Framework", "Create testing and evaluation metrics", 
                 "ML Team", TaskStatus.TODO, Priority.MEDIUM, 20),
            Task("t10", "Performance Testing", "Test system performance and accuracy", 
                 "QA Team", TaskStatus.TODO, Priority.HIGH, 30, dependencies=["t8", "t9"]),
            Task("t11", "UI Development", "Build user interface", 
                 "Frontend Team", TaskStatus.TODO, Priority.MEDIUM, 40),
            Task("t12", "API Development", "Create REST API endpoints", 
                 "Backend Team", TaskStatus.TODO, Priority.MEDIUM, 32, dependencies=["t8"]),
            Task("t13", "Security Implementation", "Add authentication and security measures", 
                 "Security Team", TaskStatus.TODO, Priority.HIGH, 24),
            Task("t14", "Deployment Setup", "Configure production environment", 
                 "DevOps Team", TaskStatus.TODO, Priority.HIGH, 32),
            Task("t15", "Documentation", "Create user and technical documentation", 
                 "Technical Writer", TaskStatus.TODO, Priority.MEDIUM, 20)
        ]
        
        return AIProject(
            id=f"rag_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=project_name,
            description="RAG (Retrieval Augmented Generation) system for enhanced AI responses with source documents",
            project_type="RAG",
            status=ProjectStatus.PLANNING,
            start_date=datetime.now().strftime("%Y-%m-%d"),
            end_date=(datetime.now() + timedelta(weeks=12)).strftime("%Y-%m-%d"),
            team_members=["ML Engineer", "Data Scientist", "Backend Developer", "Frontend Developer", "DevOps Engineer"],
            milestones=milestones,
            tasks=tasks,
            tech_stack=["Python", "LangChain", "ChromaDB/Pinecone", "OpenAI/Hugging Face", "FastAPI", "React/Streamlit"],
            risks=[
                "Document quality may be inconsistent",
                "Embedding model performance on domain-specific content",
                "Vector database scalability concerns",
                "LLM API rate limits and costs",
                "User query complexity handling"
            ]
        )
    
    @staticmethod
    def create_computer_vision_project_template(project_name: str) -> AIProject:
        """Create a template for a computer vision project."""
        
        milestones = [
            Milestone("m1", "Dataset Preparation", "Collect and annotate training data", 
                     (datetime.now() + timedelta(weeks=3)).strftime("%Y-%m-%d"), TaskStatus.TODO),
            Milestone("m2", "Model Architecture", "Design and implement model architecture", 
                     (datetime.now() + timedelta(weeks=5)).strftime("%Y-%m-%d"), TaskStatus.TODO),
            Milestone("m3", "Training Complete", "Model trained and validated", 
                     (datetime.now() + timedelta(weeks=8)).strftime("%Y-%m-%d"), TaskStatus.TODO),
            Milestone("m4", "Model Optimization", "Model optimized for production", 
                     (datetime.now() + timedelta(weeks=10)).strftime("%Y-%m-%d"), TaskStatus.TODO),
            Milestone("m5", "Deployment", "Model deployed and serving predictions", 
                     (datetime.now() + timedelta(weeks=12)).strftime("%Y-%m-%d"), TaskStatus.TODO)
        ]
        
        tasks = [
            Task("t1", "Data Collection", "Gather image/video data", 
                 "Data Team", TaskStatus.TODO, Priority.HIGH, 40),
            Task("t2", "Data Annotation", "Label training data", 
                 "Data Team", TaskStatus.TODO, Priority.HIGH, 60, dependencies=["t1"]),
            Task("t3", "Data Augmentation", "Implement data augmentation pipeline", 
                 "ML Team", TaskStatus.TODO, Priority.MEDIUM, 20),
            Task("t4", "Model Architecture Design", "Design CNN/Vision Transformer architecture", 
                 "ML Team", TaskStatus.TODO, Priority.CRITICAL, 32),
            Task("t5", "Training Pipeline", "Implement training pipeline", 
                 "ML Team", TaskStatus.TODO, Priority.HIGH, 40, dependencies=["t4"]),
            Task("t6", "Model Training", "Train model on dataset", 
                 "ML Team", TaskStatus.TODO, Priority.CRITICAL, 80, dependencies=["t2", "t5"]),
            Task("t7", "Model Evaluation", "Evaluate model performance", 
                 "ML Team", TaskStatus.TODO, Priority.HIGH, 24, dependencies=["t6"]),
            Task("t8", "Model Optimization", "Optimize for inference speed", 
                 "ML Team", TaskStatus.TODO, Priority.MEDIUM, 32, dependencies=["t7"]),
            Task("t9", "API Development", "Create prediction API", 
                 "Backend Team", TaskStatus.TODO, Priority.HIGH, 40),
            Task("t10", "Frontend Integration", "Integrate with user interface", 
                 "Frontend Team", TaskStatus.TODO, Priority.MEDIUM, 32),
            Task("t11", "Performance Testing", "Test system under load", 
                 "QA Team", TaskStatus.TODO, Priority.HIGH, 24, dependencies=["t9"]),
            Task("t12", "Deployment", "Deploy to production environment", 
                 "DevOps Team", TaskStatus.TODO, Priority.HIGH, 32)
        ]
        
        return AIProject(
            id=f"cv_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=project_name,
            description="Computer Vision system for image/video analysis and classification",
            project_type="Computer Vision",
            status=ProjectStatus.PLANNING,
            start_date=datetime.now().strftime("%Y-%m-%d"),
            end_date=(datetime.now() + timedelta(weeks=14)).strftime("%Y-%m-%d"),
            team_members=["ML Engineer", "Computer Vision Specialist", "Data Scientist", "Backend Developer", "DevOps Engineer"],
            milestones=milestones,
            tasks=tasks,
            tech_stack=["Python", "PyTorch/TensorFlow", "OpenCV", "Pillow", "FastAPI", "Docker"],
            risks=[
                "Dataset quality and diversity",
                "Model overfitting to training data",
                "Computational resource requirements",
                "Real-world performance vs lab performance",
                "Data privacy and compliance issues"
            ]
        )


class ProjectDashboard:
    """Main dashboard for project management."""
    
    def __init__(self):
        self.projects: Dict[str, AIProject] = {}
        self._load_projects()
    
    def _load_projects(self):
        """Load projects from session state or initialize empty."""
        if 'ai_projects' not in st.session_state:
            st.session_state.ai_projects = {}
        self.projects = st.session_state.ai_projects
    
    def _save_projects(self):
        """Save projects to session state."""
        st.session_state.ai_projects = self.projects
    
    def create_project(self, project: AIProject):
        """Add a new project."""
        self.projects[project.id] = project
        self._save_projects()
    
    def update_task_status(self, project_id: str, task_id: str, new_status: TaskStatus):
        """Update task status."""
        if project_id in self.projects:
            for task in self.projects[project_id].tasks:
                if task.id == task_id:
                    task.status = new_status
                    break
            self._save_projects()
    
    def render_project_overview(self):
        """Render project overview dashboard."""
        st.header("🚀 AI Project Dashboard")
        
        if not self.projects:
            st.info("No projects yet. Create your first AI project below!")
            return
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_projects = len(self.projects)
        active_projects = len([p for p in self.projects.values() if p.status == ProjectStatus.IN_PROGRESS])
        completed_projects = len([p for p in self.projects.values() if p.status == ProjectStatus.COMPLETED])
        
        with col1:
            st.metric("Total Projects", total_projects)
        with col2:
            st.metric("Active Projects", active_projects)
        with col3:
            st.metric("Completed", completed_projects)
        with col4:
            completion_rate = (completed_projects / total_projects * 100) if total_projects > 0 else 0
            st.metric("Success Rate", f"{completion_rate:.1f}%")
        
        # Project status distribution
        status_counts = {}
        for project in self.projects.values():
            status = project.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        if status_counts:
            fig = px.pie(
                values=list(status_counts.values()),
                names=list(status_counts.keys()),
                title="Project Status Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Project timeline
        self._render_project_timeline()
        
        # Recent projects table
        st.subheader("📋 Your Projects")
        project_data = []
        for project in self.projects.values():
            project_data.append({
                "Name": project.name,
                "Type": project.project_type,
                "Status": project.status.value,
                "Progress": self._calculate_project_progress(project),
                "Team Size": len(project.team_members),
                "Tasks": len(project.tasks)
            })
        
        if project_data:
            df = pd.DataFrame(project_data)
            st.dataframe(df, use_container_width=True)
    
    def _render_project_timeline(self):
        """Render project timeline visualization."""
        st.subheader("📅 Project Timeline")
        
        timeline_data = []
        for project in self.projects.values():
            for milestone in project.milestones:
                timeline_data.append({
                    "Project": project.name,
                    "Task": milestone.title,
                    "Start": project.start_date,
                    "Finish": milestone.due_date,
                    "Status": milestone.status.value
                })
        
        if timeline_data:
            df = pd.DataFrame(timeline_data)
            fig = px.timeline(
                df,
                x_start="Start",
                x_end="Finish",
                y="Project",
                color="Status",
                title="Project Milestones Timeline"
            )
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
    
    def _calculate_project_progress(self, project: AIProject) -> str:
        """Calculate project completion percentage."""
        if not project.tasks:
            return "0%"
        
        completed_tasks = len([t for t in project.tasks if t.status == TaskStatus.DONE])
        total_tasks = len(project.tasks)
        percentage = (completed_tasks / total_tasks) * 100
        return f"{percentage:.1f}%"
    
    def render_project_details(self, project_id: str):
        """Render detailed view of a specific project."""
        if project_id not in self.projects:
            st.error("Project not found!")
            return
        
        project = self.projects[project_id]
        
        st.header(f"📊 {project.name}")
        st.write(project.description)
        
        # Project metadata
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Type:** {project.project_type}")
            st.write(f"**Status:** {project.status.value}")
        with col2:
            st.write(f"**Start Date:** {project.start_date}")
            st.write(f"**End Date:** {project.end_date or 'TBD'}")
        with col3:
            st.write(f"**Team Size:** {len(project.team_members)}")
            st.write(f"**Progress:** {self._calculate_project_progress(project)}")
        
        # Task management
        st.subheader("📝 Task Management")
        self._render_task_board(project)
        
        # Milestones
        st.subheader("🎯 Milestones")
        self._render_milestones(project)
        
        # Tech stack and risks
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🛠️ Tech Stack")
            for tech in project.tech_stack:
                st.write(f"• {tech}")
        
        with col2:
            st.subheader("⚠️ Risk Factors")
            for risk in project.risks:
                st.write(f"• {risk}")
    
    def _render_task_board(self, project: AIProject):
        """Render Kanban-style task board."""
        
        # Group tasks by status
        task_groups = {
            TaskStatus.TODO: [],
            TaskStatus.IN_PROGRESS: [],
            TaskStatus.REVIEW: [],
            TaskStatus.DONE: [],
            TaskStatus.BLOCKED: []
        }
        
        for task in project.tasks:
            task_groups[task.status].append(task)
        
        # Display in columns
        cols = st.columns(5)
        status_names = ["To Do", "In Progress", "Review", "Done", "Blocked"]
        
        for i, (status, tasks) in enumerate(task_groups.items()):
            with cols[i]:
                st.write(f"**{status_names[i]} ({len(tasks)})**")
                
                for task in tasks:
                    with st.container():
                        st.write(f"**{task.title}**")
                        st.write(f"Assignee: {task.assignee}")
                        st.write(f"Priority: {task.priority.value}")
                        st.write(f"Est: {task.estimated_hours}h")
                        
                        # Status update button
                        new_status = st.selectbox(
                            f"Status for {task.id}",
                            [s.value for s in TaskStatus],
                            index=list(TaskStatus).index(task.status),
                            key=f"status_{task.id}"
                        )
                        
                        if new_status != task.status.value:
                            self.update_task_status(project.id, task.id, TaskStatus(new_status))
                            st.rerun()
                        
                        st.divider()
    
    def _render_milestones(self, project: AIProject):
        """Render project milestones."""
        
        milestone_data = []
        for milestone in project.milestones:
            milestone_data.append({
                "Milestone": milestone.title,
                "Due Date": milestone.due_date,
                "Status": milestone.status.value,
                "Progress": f"{milestone.completion_percentage}%"
            })
        
        if milestone_data:
            df = pd.DataFrame(milestone_data)
            st.dataframe(df, use_container_width=True)


def create_project_management_app():
    """Create the main project management application."""
    
    dashboard = ProjectDashboard()
    
    st.sidebar.header("🚀 Project Management")
    
    # Navigation
    view = st.sidebar.selectbox(
        "Choose View:",
        ["Dashboard Overview", "Create New Project", "Project Details"]
    )
    
    if view == "Dashboard Overview":
        dashboard.render_project_overview()
    
    elif view == "Create New Project":
        st.header("➕ Create New AI Project")
        
        # Project type selection
        project_type = st.selectbox(
            "Choose Project Type:",
            ["RAG System", "Computer Vision", "Custom Project"]
        )
        
        project_name = st.text_input("Project Name")
        
        if st.button("Create Project") and project_name:
            if project_type == "RAG System":
                project = AIProjectTemplate.create_rag_project_template(project_name)
            elif project_type == "Computer Vision":
                project = AIProjectTemplate.create_computer_vision_project_template(project_name)
            else:
                # Create basic custom project template
                project = AIProject(
                    id=f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    name=project_name,
                    description="Custom AI project",
                    project_type="Custom",
                    status=ProjectStatus.PLANNING,
                    start_date=datetime.now().strftime("%Y-%m-%d"),
                    end_date=None,
                    team_members=["Project Lead"],
                    milestones=[],
                    tasks=[]
                )
            
            dashboard.create_project(project)
            st.success(f"Project '{project_name}' created successfully!")
            st.balloons()
    
    elif view == "Project Details":
        if dashboard.projects:
            project_names = [f"{p.name} ({p.id})" for p in dashboard.projects.values()]
            selected = st.selectbox("Select Project:", project_names)
            
            if selected:
                project_id = selected.split("(")[1].rstrip(")")
                dashboard.render_project_details(project_id)
        else:
            st.info("No projects available. Create a project first!")