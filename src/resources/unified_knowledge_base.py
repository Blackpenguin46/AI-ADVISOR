"""
Unified Knowledge Base that integrates multi-format resources with existing video knowledge.
"""

import streamlit as st
from typing import Dict, List, Any, Optional
from .multi_format_ingestor import ResourceManager

try:
    from .daily_dev_integration import create_daily_dev_interface
    DAILY_DEV_BASIC_AVAILABLE = True
except ImportError:
    DAILY_DEV_BASIC_AVAILABLE = False

try:
    from .scheduled_sync import create_scheduled_sync_interface
    SCHEDULED_SYNC_AVAILABLE = True
except ImportError:
    SCHEDULED_SYNC_AVAILABLE = False

try:
    from .comprehensive_scraper import create_comprehensive_scraper_interface
    COMPREHENSIVE_SCRAPER_AVAILABLE = True
except ImportError:
    COMPREHENSIVE_SCRAPER_AVAILABLE = False

DAILY_DEV_AVAILABLE = DAILY_DEV_BASIC_AVAILABLE


class UnifiedKnowledgeBase:
    """Unified knowledge base supporting multiple resource formats."""
    
    def __init__(self, data_directory: str = "data"):
        self.resource_manager = ResourceManager(data_directory)
    
    def search_knowledge(self, query: str, n_results: int = 5, source_types: List[str] = None) -> List[Dict[str, Any]]:
        """Search across all resources in the knowledge base."""
        return self.resource_manager.search_resources(query, n_results, source_types)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive knowledge base statistics."""
        stats = self.resource_manager.get_resource_stats()
        
        return {
            'total_chunks': stats['total_chunks'],
            'total_resources': stats['total_resources'],
            'by_type': stats['enhanced_by_type'],  # Use enhanced counts with Daily.dev
            'daily_dev_count': stats['daily_dev_count'],
            'supported_formats': stats['supported_formats'],
            'missing_dependencies': stats['missing_dependencies']
        }
    
    def add_resource(self, source, source_type: str, title: str = None, 
                    author: str = None, description: str = None, tags: List[str] = None) -> bool:
        """Add a new resource to the knowledge base."""
        return self.resource_manager.add_resource(source, source_type, title, author, description, tags)
    
    def remove_resource(self, resource_id: str) -> bool:
        """Remove a resource from the knowledge base."""
        return self.resource_manager.remove_resource(resource_id)
    
    def get_all_resources(self) -> Dict[str, Any]:
        """Get all resources metadata."""
        return {
            resource_id: resource_data['metadata'] 
            for resource_id, resource_data in self.resource_manager.knowledge_base.items()
        }
    
    def get_resource_by_id(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific resource by ID."""
        return self.resource_manager.knowledge_base.get(resource_id)


def create_resource_management_interface():
    """Create the resource management interface."""
    
    st.header("📚 Resource Management")
    st.write("Add and manage your knowledge base resources")
    
    # Initialize unified knowledge base
    if 'unified_kb' not in st.session_state:
        with st.spinner("Loading unified knowledge base..."):
            st.session_state.unified_kb = UnifiedKnowledgeBase()
    
    kb = st.session_state.unified_kb
    
    # Show current stats
    stats = kb.get_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Resources", stats['total_resources'])
    with col2:
        st.metric("Total Chunks", stats['total_chunks'])
    with col3:
        st.metric("Resource Types", len(stats['by_type']))
    with col4:
        coverage = len([f for f, available in stats['supported_formats'].items() if available])
        st.metric("Supported Formats", f"{coverage}/7")
    
    # Show resource breakdown
    if stats['by_type']:
        st.subheader("📊 Resources by Type")
        for resource_type, count in stats['by_type'].items():
            st.write(f"**{resource_type.upper()}**: {count} resources")
    
    # Show missing dependencies
    if stats['missing_dependencies']:
        st.warning("**Missing Dependencies for Full Functionality:**")
        for dep in stats['missing_dependencies']:
            st.write(f"• {dep}")
        st.info("Install missing dependencies with: `pip install PyPDF2 python-docx beautifulsoup4 markdown`")
    
    st.divider()
    
    # Add new resources
    st.subheader("➕ Add New Resources")
    
    tabs = ["📄 Upload Files", "🌐 Add URLs", "📝 Add Text", "🎥 Legacy Videos"]
    if DAILY_DEV_AVAILABLE:
        tabs.append("📰 Daily.dev")
    
    if DAILY_DEV_AVAILABLE:
        tab1, tab2, tab3, tab4, tab5 = st.tabs(tabs)
    else:
        tab1, tab2, tab3, tab4 = st.tabs(tabs)
    
    with tab1:
        st.write("**Upload PDF, DOCX, or text files**")
        
        uploaded_files = st.file_uploader(
            "Choose files",
            type=['pdf', 'docx', 'txt', 'md'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                with st.expander(f"Configure: {uploaded_file.name}"):
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        title = st.text_input(f"Title for {uploaded_file.name}", 
                                            value=uploaded_file.name.split('.')[0], 
                                            key=f"title_{uploaded_file.name}")
                        author = st.text_input(f"Author", key=f"author_{uploaded_file.name}")
                    
                    with col_b:
                        description = st.text_area(f"Description", key=f"desc_{uploaded_file.name}")
                        tags = st.text_input(f"Tags (comma-separated)", 
                                           placeholder="ai, machine learning, tutorial",
                                           key=f"tags_{uploaded_file.name}")
                    
                    if st.button(f"Add {uploaded_file.name}", key=f"add_{uploaded_file.name}"):
                        with st.spinner(f"Processing {uploaded_file.name}..."):
                            # Determine file type
                            file_extension = uploaded_file.name.split('.')[-1].lower()
                            
                            # Read file content
                            file_content = uploaded_file.read()
                            
                            # Process tags
                            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []
                            
                            # Add to knowledge base
                            success = kb.add_resource(
                                source=file_content,
                                source_type=file_extension,
                                title=title,
                                author=author if author else None,
                                description=description if description else None,
                                tags=tag_list
                            )
                            
                            if success:
                                st.success(f"✅ Successfully added {uploaded_file.name}")
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to add {uploaded_file.name}")
    
    with tab2:
        st.write("**Add web pages and online resources**")
        
        url = st.text_input("URL", placeholder="https://example.com/article")
        
        col_a, col_b = st.columns(2)
        with col_a:
            url_title = st.text_input("Title (auto-detected if empty)")
            url_author = st.text_input("Author/Source")
        
        with col_b:
            url_description = st.text_area("Description")
            url_tags = st.text_input("Tags (comma-separated)", 
                                   placeholder="web, article, tutorial")
        
        if st.button("Add URL Resource") and url:
            with st.spinner("Fetching and processing URL..."):
                tag_list = [tag.strip() for tag in url_tags.split(',') if tag.strip()] if url_tags else []
                
                success = kb.add_resource(
                    source=url,
                    source_type='url',
                    title=url_title if url_title else None,
                    author=url_author if url_author else None,
                    description=url_description if url_description else None,
                    tags=tag_list
                )
                
                if success:
                    st.success("✅ Successfully added URL resource")
                    st.rerun()
                else:
                    st.error("❌ Failed to add URL resource")
    
    with tab3:
        st.write("**Add text content directly**")
        
        text_content = st.text_area("Text Content", height=200, 
                                  placeholder="Paste your text content here...")
        
        col_a, col_b = st.columns(2)
        with col_a:
            text_title = st.text_input("Title", key="text_title")
            text_author = st.text_input("Author", key="text_author")
        
        with col_b:
            text_description = st.text_area("Description", key="text_desc")
            text_tags = st.text_input("Tags (comma-separated)", key="text_tags")
        
        if st.button("Add Text Content") and text_content and text_title:
            tag_list = [tag.strip() for tag in text_tags.split(',') if tag.strip()] if text_tags else []
            
            success = kb.add_resource(
                source=text_content,
                source_type='text',
                title=text_title,
                author=text_author if text_author else None,
                description=text_description if text_description else None,
                tags=tag_list
            )
            
            if success:
                st.success("✅ Successfully added text content")
                st.rerun()
            else:
                st.error("❌ Failed to add text content")
    
    with tab4:
        st.write("**Manage existing video resources**")
        
        # Show video resources
        all_resources = kb.get_all_resources()
        video_resources = {rid: meta for rid, meta in all_resources.items() 
                          if meta['source_type'] == 'video'}
        
        if video_resources:
            st.write(f"**Found {len(video_resources)} video resources**")
            
            for resource_id, metadata in list(video_resources.items())[:10]:  # Show first 10
                with st.expander(f"🎥 {metadata['title'][:60]}..."):
                    col_a, col_b = st.columns([3, 1])
                    
                    with col_a:
                        st.write(f"**Author:** {metadata.get('author', 'Unknown')}")
                        st.write(f"**URL:** {metadata['source_url']}")
                        st.write(f"**Added:** {metadata.get('date_added', 'Unknown')}")
                        if metadata.get('description'):
                            st.write(f"**Description:** {metadata['description'][:200]}...")
                    
                    with col_b:
                        if st.button("🗑️ Remove", key=f"remove_{resource_id}"):
                            if kb.remove_resource(resource_id):
                                st.success("Resource removed")
                                st.rerun()
                            else:
                                st.error("Failed to remove resource")
        else:
            st.info("No video resources found. Your original video knowledge base will be automatically converted when you first run the enhanced system.")
    
    # Daily.dev integration tab
    if DAILY_DEV_AVAILABLE:
        with tab5:
            # Determine available features
            available_features = []
            if DAILY_DEV_BASIC_AVAILABLE:
                available_features.append("Basic Sync")
            if COMPREHENSIVE_SCRAPER_AVAILABLE:
                available_features.append("Comprehensive Scraping")
            if SCHEDULED_SYNC_AVAILABLE:
                available_features.append("Scheduled Sync")
            
            if not available_features:
                st.error("Daily.dev features not available. Install MCP dependencies.")
                st.code("pip install mcp selenium webdriver-manager fastmcp")
            else:
                daily_dev_tab = st.selectbox(
                    "Daily.dev Feature:",
                    available_features
                )
                
                if daily_dev_tab == "Basic Sync" and DAILY_DEV_BASIC_AVAILABLE:
                    create_daily_dev_interface(kb)
                elif daily_dev_tab == "Comprehensive Scraping" and COMPREHENSIVE_SCRAPER_AVAILABLE:
                    create_comprehensive_scraper_interface(kb)
                elif daily_dev_tab == "Scheduled Sync" and SCHEDULED_SYNC_AVAILABLE:
                    create_scheduled_sync_interface(kb)
                else:
                    st.error(f"Feature '{daily_dev_tab}' not available. Check dependencies.")
    
    st.divider()
    
    # Resource browser
    st.subheader("🔍 Browse Resources")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        resource_types = list(stats['by_type'].keys()) if stats['by_type'] else []
        selected_types = st.multiselect("Filter by Type", resource_types, default=resource_types)
    
    with col2:
        sort_by = st.selectbox("Sort by", ["Date Added", "Title", "Type"])
    
    with col3:
        search_term = st.text_input("Search Resources", placeholder="Enter keywords...")
    
    # Show filtered resources
    all_resources = kb.get_all_resources()
    
    if search_term:
        # Search in titles and descriptions
        filtered_resources = {
            rid: meta for rid, meta in all_resources.items()
            if (search_term.lower() in meta['title'].lower() or
                search_term.lower() in meta.get('description', '').lower())
            and meta['source_type'] in selected_types
        }
    else:
        filtered_resources = {
            rid: meta for rid, meta in all_resources.items()
            if meta['source_type'] in selected_types
        }
    
    if filtered_resources:
        st.write(f"**Showing {len(filtered_resources)} resources**")
        
        # Display resources
        for resource_id, metadata in list(filtered_resources.items())[:20]:  # Limit to 20
            with st.expander(f"{metadata['source_type'].upper()}: {metadata['title'][:80]}"):
                col_a, col_b = st.columns([4, 1])
                
                with col_a:
                    st.write(f"**Type:** {metadata['source_type']}")
                    st.write(f"**Author:** {metadata.get('author', 'Unknown')}")
                    st.write(f"**Added:** {metadata.get('date_added', 'Unknown')}")
                    
                    if metadata.get('description'):
                        st.write(f"**Description:** {metadata['description']}")
                    
                    if metadata.get('tags'):
                        st.write(f"**Tags:** {', '.join(metadata['tags'])}")
                    
                    if metadata['source_type'] == 'url':
                        st.markdown(f"🔗 [View Source]({metadata['source_url']})")
                
                with col_b:
                    if st.button("🗑️ Remove", key=f"remove_browse_{resource_id}"):
                        if kb.remove_resource(resource_id):
                            st.success("Resource removed")
                            st.rerun()
                        else:
                            st.error("Failed to remove resource")
    else:
        st.info("No resources found matching your criteria.")