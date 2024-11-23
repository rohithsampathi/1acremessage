# components/ui.py

import pandas as pd
from typing import Dict, Any
import streamlit as st

class UIComponents:
    @staticmethod
    def render_metric_card(value: Any, label: str) -> str:
        """Render a metric card with consistent styling"""
        return f"""
        <div class="metric-card">
            <div class="metric-value">{value}</div>
            <div class="metric-label">{label}</div>
        </div>
        """
    
    @staticmethod
    def render_conversation_card(conv: pd.Series, is_selected: bool, key_prefix: str) -> None:
        """
        Render a conversation card with improved visibility
        
        Args:
            conv: Series containing conversation data
            is_selected: Boolean indicating if conversation is selected
            key_prefix: Unique prefix for component keys
        """
        try:
            # Create an expander for each conversation
            with st.expander(f"💬 Conversation with {conv['Name of the Profile']}"):
                # Display conversation metadata
                st.markdown(f"""
                    **Profile ID:** {conv['Profile ID']}\n
                    **First Contact:** {conv['First Contact Date and Time'].strftime('%Y-%m-%d %H:%M')}\n
                    **Messages:** {conv['Message Count']}\n
                    **Duration:** {conv['Conversation Length (Days)']} days
                """)
                
                # Display the full conversation with better formatting
                st.markdown("### Conversation Content")
                conversation_text = conv['Conversation'].replace('[1acre]:', '**1acre:**').replace(
                    '[Customer]:', '**Customer:**')
                st.markdown(conversation_text)
                
                # Add selection/deselection button
                if not is_selected:
                    if st.button("Select Conversation", key=f"select_{key_prefix}"):
                        if 'selected_chats' not in st.session_state:
                            st.session_state.selected_chats = []
                        st.session_state.selected_chats.append(conv.to_dict())
                        st.rerun()
                else:
                    if st.button("Remove from Selection", key=f"remove_{key_prefix}"):
                        st.session_state.selected_chats = [
                            chat for chat in st.session_state.selected_chats 
                            if chat['Profile ID'] != conv['Profile ID']
                        ]
                        st.rerun()
                
        except Exception as e:
            st.error(f"Error rendering conversation: {str(e)}")
    
    @staticmethod
    def render_selected_chats_summary(selected_chats: list) -> None:
        """Render summary of selected conversations"""
        if not selected_chats:
            return
        
        st.markdown("### 📋 Selected Conversations")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Selected", len(selected_chats))
        with col2:
            total_messages = sum(chat['Message Count'] for chat in selected_chats)
            st.metric("Total Messages", total_messages)
        with col3:
            avg_length = sum(chat['Conversation Length (Days)'] for chat in selected_chats) / len(selected_chats)
            st.metric("Average Duration (Days)", f"{avg_length:.1f}")
        
        # Download options
        st.markdown("#### Download Options")
        if st.button("Download Selected Conversations"):
            content = "\n\n".join([
                f"=== Conversation with {chat['Name of the Profile']} ===\n"
                f"Date: {chat['First Contact Date and Time']}\n"
                f"Duration: {chat['Conversation Length (Days)']} days\n"
                f"Messages: {chat['Message Count']}\n\n"
                f"{chat['Conversation']}\n"
                f"{'='*50}"
                for chat in selected_chats
            ])
            
            st.download_button(
                label="Save as TXT",
                data=content,
                file_name="selected_conversations.txt",
                mime="text/plain"
            )
        
        if st.button("Clear Selection"):
            st.session_state.selected_chats = []
            st.rerun()