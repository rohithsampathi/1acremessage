# streamlit_dashboard.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from components.metrics import MetricsAnalyzer
from components.search import ConversationSearch
from components.ui import UIComponents
from utils.data_loader import DataLoader
import auth

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class FilterState:
    date_range: Optional[Tuple[datetime, datetime]] = None
    min_messages: int = 1
    sort_by: str = 'Recent'
    query: str = ''

class DashboardApp:
    def __init__(self):
        """Initialize dashboard application"""
        # Initialize session state first
        self._init_session_state()
        
        # Set page config with metadata
        st.set_page_config(
            page_title="1acre Message Analytics | Conversation Intelligence Platform",
            page_icon="🏙️",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                'Get Help': 'mailto:support@1acre.in',
                'Report a bug': 'mailto:support@1acre.in',
                'About': """
                # 1acre Message Analytics
                A powerful conversation intelligence platform for analyzing customer interactions.
                
                Version: 1.0.0
                © 2024 1acre
                """
            }
        )
        
        # Initialize components
        self.data_loader = DataLoader()
        self.ui = UIComponents()
        self.metrics = None
        
        # Load custom CSS
        with open('style.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

        # Set additional metadata
        st.markdown(
            """
            <meta name="description" content="1acre Message Analytics - Advanced conversation intelligence platform for analyzing customer interactions and deriving actionable insights.">
            <meta name="keywords" content="1acre, analytics, conversation intelligence, customer interactions, real estate">
            <meta name="author" content="1acre">
            """,
            unsafe_allow_html=True
        )
        
        # Force dark theme
        st.markdown("""
            <script>
                document.documentElement.style.setProperty('--primary-color', '#4CAF50');
                document.documentElement.style.setProperty('--secondary-color', '#2E7D32');
                document.documentElement.style.setProperty('--background-color', '#1E1E1E');
                document.documentElement.style.setProperty('--text-color', '#FFFFFF');
            </script>
            """, 
            unsafe_allow_html=True
        )
    
    def _init_session_state(self) -> None:
        """Initialize all session state variables"""
        if 'initialized' not in st.session_state:
            st.session_state.initialized = True
            st.session_state.logged_in = False
            st.session_state.selected_chats = []
            st.session_state.search_results = pd.DataFrame()
            st.session_state.filters = FilterState()
            st.session_state.current_view = 'overview'
            st.session_state.last_search = None
            st.session_state.page_number = 1
            st.session_state.items_per_page = 10
    
    def handle_auth(self) -> None:
        """Handle user authentication"""
        st.markdown("""
            <div class="login-header">
                <h1>🏙️ 1acre Message Analytics</h1>
                <p>Conversation Intelligence Platform</p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            with st.form("login", clear_on_submit=True):
                username = st.text_input("Email", placeholder="Enter your email")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submit = st.form_submit_button("Login")
                
                if submit:
                    if auth.authenticate(username, password):
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.error("Invalid credentials")

    def _format_message(self, msg: str) -> Dict[str, str]:
        """Format message for display"""
        try:
            if msg.startswith('['):
                sender, content = msg.split(':', 1)
                sender = sender.strip('[]')
                sender = '1acre' if 'acre' in sender.lower() else 'Customer'
                return {
                    'sender': sender,
                    'content': content.strip(),
                    'style': f'message-{sender.lower()}'
                }
            return {
                'sender': 'Customer',
                'content': msg,
                'style': 'message-customer'
            }
        except Exception as e:
            logger.error(f"Message format error: {e}")
            return {
                'sender': 'Error',
                'content': msg,
                'style': 'message-error'
            }

    def _render_message(self, msg: Dict[str, str]) -> None:
        """Render a single message"""
        st.markdown(
            f'<div class="message {msg["style"]}">'
            f'<div class="sender sender-{msg["style"]}">{msg["sender"]}</div>'
            f'<div class="message-content">{msg["content"]}</div>'
            '</div>',
            unsafe_allow_html=True
        )

    def render_overview(self, df: pd.DataFrame) -> None:
        """Render overview page"""
        try:
            if not self.metrics:
                self.metrics = MetricsAnalyzer(df)
            
            # Display metrics
            cols = st.columns(4)
            for col, (key, value) in zip(cols, self.metrics.get_overview_metrics().items()):
                with col:
                    st.markdown(self.ui.render_metric_card(value, key), unsafe_allow_html=True)

            # Display charts
            st.plotly_chart(self.metrics.create_timeline_chart(), use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(self.metrics.create_activity_heatmap(), use_container_width=True)
            with col2:
                st.plotly_chart(self.metrics.create_conversation_length_chart(), use_container_width=True)
        except Exception as e:
            logger.error(f"Overview error: {e}")
            st.error("Error displaying overview")

    def render_conversations(self, df: pd.DataFrame) -> None:
        """Render conversations page"""
        try:
            search = ConversationSearch(df)
            search_params = search.get_search_interface()
            
            if search_params.get('search_clicked'):
                with st.spinner("Searching conversations..."):
                    results = search.search(
                        query=search_params['query'],
                        date_range=search_params['date_range'],
                        min_messages=search_params['min_messages'],
                        sort_by=search_params['sort_by']
                    )
                    
                    if not results.empty:
                        st.session_state.search_results = results
                        st.success(f"Found {len(results)} conversations")
                    else:
                        st.info("No matching conversations found")
                        st.session_state.search_results = pd.DataFrame()

            # Display selected chats summary
            if st.session_state.selected_chats:
                self.ui.render_selected_chats_summary(st.session_state.selected_chats)
                st.markdown("---")

            # Display search results
            if not st.session_state.search_results.empty:
                for idx, conv in st.session_state.search_results.iterrows():
                    is_selected = any(
                        chat['Profile ID'] == conv['Profile ID'] 
                        for chat in st.session_state.selected_chats
                    )
                    
                    with st.expander(
                        f"💬 {conv['Name of the Profile']} - {conv['Message Count']} messages",
                        expanded=False
                    ):
                        # Metadata section
                        st.markdown(f"""
                            **Profile:** {conv['Name of the Profile']}\n
                            **ID:** {conv['Profile ID']}\n
                            **First Contact:** {conv['First Contact Date and Time'].strftime('%Y-%m-%d %H:%M')}\n
                            **Duration:** {conv['Conversation Length (Days)']} days
                        """)
                        
                        # Conversation content
                        st.markdown('<div class="conversation-text">', unsafe_allow_html=True)
                        for message in conv['Conversation'].split('\n'):
                            if message.strip():
                                self._render_message(self._format_message(message))
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Selection buttons
                        col1, col2, col3 = st.columns([1, 1, 2])
                        with col1:
                            if not is_selected:
                                if st.button("📌 Select", key=f"sel_{idx}"):
                                    st.session_state.selected_chats.append(conv.to_dict())
                                    st.rerun()
                            else:
                                if st.button("❌ Remove", key=f"rem_{idx}"):
                                    st.session_state.selected_chats = [
                                        chat for chat in st.session_state.selected_chats 
                                        if chat['Profile ID'] != conv['Profile ID']
                                    ]
                                    st.rerun()
                        
        except Exception as e:
            logger.error(f"Conversation error: {e}")
            st.error("Error displaying conversations")

    def render_analytics(self, df: pd.DataFrame) -> None:
        """Render analytics page"""
        try:
            if not self.metrics:
                self.metrics = MetricsAnalyzer(df)
            
            time_range = st.selectbox(
                "Time Range",
                ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"]
            )
            
            if time_range != "All Time":
                days = int(time_range.split()[1])
                df = df[
                    df['First Contact Date and Time'] >= 
                    (datetime.now() - timedelta(days=days))
                ]

            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(
                    self.metrics.create_timeline_chart(),
                    use_container_width=True
                )
                st.plotly_chart(
                    self.metrics.create_conversation_length_chart(),
                    use_container_width=True
                )
            with col2:
                st.plotly_chart(
                    self.metrics.create_activity_heatmap(),
                    use_container_width=True
                )
                
                # Display metrics in a grid
                metrics_data = self.metrics.get_overview_metrics()
                metric_cols = st.columns(2)
                for i, (key, value) in enumerate(metrics_data.items()):
                    with metric_cols[i % 2]:
                        st.metric(key, value)
                        
        except Exception as e:
            logger.error(f"Analytics error: {e}")
            st.error("Error displaying analytics")

    def run(self) -> None:
        """Run the dashboard application"""
        try:
            if not st.session_state.logged_in:
                self.handle_auth()
                return

            # Sidebar navigation
            with st.sidebar:
                st.markdown("### Navigation")
                view = st.radio(
                    "Select View",
                    ["Overview", "Conversations", "Analytics"]
                )
                
                if st.button("Logout"):
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    self._init_session_state()
                    st.rerun()

            # Load and process data
            df = self.data_loader.load_data("instagram_conversations.xlsx")
            if df.empty:
                st.error("No data available")
                return

            # Render selected view
            view_mapping = {
                "Overview": self.render_overview,
                "Conversations": self.render_conversations,
                "Analytics": self.render_analytics
            }
            view_mapping[view](df)

        except Exception as e:
            logger.error(f"Application error: {e}")
            st.error("An error occurred. Please try again.")

if __name__ == "__main__":
    DashboardApp().run()