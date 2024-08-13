import streamlit as st
import pandas as pd
import re
from multiprocessing import Pool, cpu_count

# Set page config at the very beginning
st.set_page_config(page_title="1acre Message Board", layout="wide", page_icon="🏙️")

# Custom CSS for futuristic, bold, minimalistic white and grey theme
st.markdown("""
<style>
    body {
        color: #FFFFFF;
        background-color: #121212;
    }
    .stApp {
        background-color: #121212;
    }
    .stTextInput > div > div > input {
        background-color: #2C2C2C;
        color: #FFFFFF;
        border: 1px solid #4A4A4A;
    }
    .stTextArea > div > div > textarea {
        background-color: #2C2C2C;
        color: #FFFFFF;
        border: 1px solid #4A4A4A;
    }
    .stButton > button {
        background-color: #4A4A4A;
        color: #FFFFFF;
        border: none;
    }
    .stExpander {
        background-color: #2C2C2C;
        border: 1px solid #4A4A4A;
    }
    .stExpander > div > div > div > div > div > p {
        color: #FFFFFF;
    }
    h1, h2, h3 {
        color: #00FF00;
    }
    p {
        color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(file_path):
    return pd.read_excel(file_path)

def preprocess_text(text):
    return re.sub(r'[^\w\s]', '', str(text).lower())

def search_term(args):
    df, term = args
    term = preprocess_text(term)
    mask = df['processed_conversation'].str.contains(r'\b' + re.escape(term) + r'\b', regex=True)
    return df[mask]

def parallel_search_conversations(df, search_terms):
    with Pool(processes=min(cpu_count(), len(search_terms))) as pool:
        results = pool.map(search_term, [(df, term) for term in search_terms])
    
    common_results = pd.concat(results).groupby(level=0).filter(lambda x: len(x) == len(search_terms))
    # Remove duplicate conversations
    unique_results = common_results.drop_duplicates(subset=['Conversation'])
    return unique_results

def main():
    # Custom title with emoji
    st.markdown("# 🏙️ 1acre Message Board")
    st.markdown("### Discover Your Perfect Land")

    # Load data
    file_path = "./instagram_conversations.xlsx"
    try:
        df = load_data(file_path)
        st.success("Data loaded successfully!")
        df['processed_conversation'] = df['Conversation'].astype(str).apply(preprocess_text)
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        st.info("Please ensure the data file is present and properly named.")
        return

    # Search functionality
    st.markdown("## 🔍 Search Conversations")
    search_query = st.text_input("Enter search terms (separate multiple terms with spaces)")
    search_terms = [term.strip() for term in search_query.split() if term.strip()]

    if st.button("Search", key="search_button"):
        if search_terms:
            results = parallel_search_conversations(df, search_terms)
            if not results.empty:
                st.markdown(f"### 📊 Search Results: {len(results)} unique conversations found")
                for i, (_, row) in enumerate(results.iterrows()):
                    with st.expander(f"💬 {row['Name of the Profile']} - {row['First Contact Date and Time']}"):
                        st.text_area("Conversation", row['Conversation'], height=200, key=f"conversation_{i}")
            else:
                st.info("No matching conversations found.")
        else:
            st.warning("Please enter search terms to begin.")

if __name__ == "__main__":
    main()