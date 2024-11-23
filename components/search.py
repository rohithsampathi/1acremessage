# components/search.py

import pandas as pd
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
import streamlit as st
from multiprocessing import Pool, cpu_count
import re
import logging

logger = logging.getLogger(__name__)

class ConversationSearch:
    def __init__(self, df: pd.DataFrame):
        """Initialize search with conversation DataFrame"""
        self.df = df.copy()
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for search"""
        try:
            return re.sub(r'[^\w\s]', '', str(text).lower())
        except Exception as e:
            logger.error(f"Error preprocessing text: {e}")
            return str(text).lower()

    def _search_term(self, args: Tuple[pd.DataFrame, str]) -> pd.DataFrame:
        """Helper function for parallel search"""
        try:
            df, term = args
            term = self.preprocess_text(term)
            mask = (
                df['processed_conversation'].str.contains(r'\b' + re.escape(term) + r'\b', regex=True, na=False) |
                df['Name of the Profile'].str.contains(term, case=False, na=False) |
                df['Profile ID'].str.contains(term, case=False, na=False)
            )
            return df[mask]
        except Exception as e:
            logger.error(f"Error in search term processing: {e}")
            return pd.DataFrame()

    def search(self, 
              query: Optional[str] = None, 
              date_range: Optional[Tuple[datetime, datetime]] = None,
              min_messages: int = 1,
              sort_by: str = "Recent",
              max_results: int = 100) -> pd.DataFrame:
        """
        Search conversations with parallel processing
        
        Args:
            query: Search string for conversation content or profile info
            date_range: Tuple of (start_date, end_date) for filtering
            min_messages: Minimum number of messages in conversation
            sort_by: Sorting criteria
            max_results: Maximum number of results to return
        """
        try:
            filtered_df = self.df.copy()
            
            # Apply date range filter
            if date_range and all(date_range):
                start_date, end_date = date_range
                filtered_df = filtered_df[
                    (filtered_df['First Contact Date and Time'].dt.date >= start_date) &
                    (filtered_df['First Contact Date and Time'].dt.date <= end_date)
                ]
            
            # Apply message count filter
            filtered_df = filtered_df[filtered_df['Message Count'] >= min_messages]
            
            # Process search terms in parallel
            if query:
                search_terms = [term.strip() for term in query.split() if term.strip()]
                if search_terms:
                    with Pool(processes=min(cpu_count(), len(search_terms))) as pool:
                        results = pool.map(
                            self._search_term,
                            [(filtered_df, term) for term in search_terms]
                        )
                        
                        # Combine and filter results
                        if results:
                            matches = pd.concat(results)
                            filtered_df = (matches.groupby(level=0)
                                         .filter(lambda x: len(x) == len(search_terms))
                                         .drop_duplicates())
                        else:
                            return pd.DataFrame()
            
            # Sort results
            filtered_df = self.sort_conversations(filtered_df, sort_by)
            
            # Limit results
            return filtered_df.head(max_results)
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            st.error("Error performing search")
            return pd.DataFrame()
    
    def sort_conversations(self, df: pd.DataFrame, sort_by: str) -> pd.DataFrame:
        """Sort conversations based on criteria"""
        try:
            sort_options = {
                "Recent": ('Last Contact Date and Time', False),
                "Oldest": ('First Contact Date and Time', True),
                "Most Messages": ('Message Count', False),
                "Longest Duration": ('Conversation Length (Days)', False)
            }
            
            if sort_by in sort_options:
                column, ascending = sort_options[sort_by]
                return df.sort_values(column, ascending=ascending)
            return df
            
        except Exception as e:
            logger.error(f"Sorting error: {e}")
            return df

    def get_search_interface(self) -> Dict[str, Any]:
        """Create a unified search interface"""
        try:
            st.markdown("### 🔍 Search Conversations")
            
            # Create three columns for search inputs
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                query = st.text_input(
                    "Search terms",
                    placeholder="Enter keywords (space-separated)..."
                )
            
            with col2:
                min_messages = st.number_input(
                    "Min messages",
                    min_value=1,
                    value=1
                )
            
            with col3:
                sort_by = st.selectbox(
                    "Sort by",
                    ["Recent", "Oldest", "Most Messages", "Longest Duration"]
                )
            
            # Date range filter in expander
            with st.expander("📅 Date Range Filter", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Start date", value=None)
                with col2:
                    end_date = st.date_input("End date", value=None)
            
            # Center the search button
            cols = st.columns([3, 1, 3])
            with cols[1]:
                search_clicked = st.button("🔍 Search", use_container_width=True)
            
            return {
                'query': query,
                'date_range': (start_date, end_date) if start_date and end_date else None,
                'min_messages': min_messages,
                'sort_by': sort_by,
                'search_clicked': search_clicked
            }
            
        except Exception as e:
            logger.error(f"Error in search interface: {e}")
            st.error("Error displaying search interface")
            return {}