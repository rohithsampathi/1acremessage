# utils/data_loader.py

import pandas as pd
import streamlit as st
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self):
        self._last_load_time = None
    
    @staticmethod
    @st.cache_resource(show_spinner=False)
    def _load_excel_file(file_path: str) -> Optional[pd.DataFrame]:
        """Load Excel file with resource caching"""
        try:
            return pd.read_excel(file_path)
        except Exception as e:
            logger.error(f"Error loading Excel file: {e}")
            return None

    def load_data(self, file_path: str) -> pd.DataFrame:
        """Load and preprocess the Excel data"""
        try:
            # Load data using resource caching
            df = self._load_excel_file(file_path)
            
            if df is None:
                logger.error("Failed to load data file")
                return pd.DataFrame()
            
            with st.spinner("Processing data..."):
                # Process datetime columns
                datetime_cols = ['First Contact Date and Time', 'Last Contact Date and Time']
                for col in datetime_cols:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                
                # Create processed conversation column for search
                df['processed_conversation'] = (
                    df['Conversation']
                    .astype(str)
                    .str.lower()
                    .str.replace(r'[^\w\s]', '', regex=True)
                )
                
                # Sort by first contact date
                df.sort_values('First Contact Date and Time', ascending=False, inplace=True)
            
            self._last_load_time = datetime.now()
            logger.info(f"Successfully loaded {len(df)} conversations")
            
            return df
            
        except Exception as e:
            logger.error(f"Error in data loading: {e}")
            st.error("Error loading data. Please check the file.")
            return pd.DataFrame()
    
    @staticmethod
    def clear_cache() -> None:
        """Clear the cached data"""
        try:
            st.cache_resource.clear()
            logger.info("Cache cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")