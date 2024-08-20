import streamlit as st
import pandas as pd
import re
from multiprocessing import Pool, cpu_count
import auth
import io

# Set page config at the very beginning
st.set_page_config(page_title="1acre Message Board", layout="wide", page_icon="🏙️")

# Custom CSS with updated button styling
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
    transition: background-color 0.3s ease;
}
.stButton > button:hover {
    background-color: #FF0000;
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
/* Ensure download button matches other buttons */
.stDownloadButton > button {
    background-color: #4A4A4A;
    color: #FFFFFF;
    border: none;
    transition: background-color 0.3s ease;
}
.stDownloadButton > button:hover {
    background-color: #FF0000;
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
    unique_results = common_results.drop_duplicates(subset=['Conversation'])
    return unique_results

def download_selected_chats(selected_chats):
    content = "\n\n".join([f"Chat with {chat['Name of the Profile']} on {chat['First Contact Date and Time']}:\n{chat['Conversation']}" for chat in selected_chats])
    return content

def main():
    st.markdown("# 🏙️ 1acre Message Board")
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'selected_chats' not in st.session_state:
        st.session_state.selected_chats = []
    if 'search_results' not in st.session_state:
        st.session_state.search_results = pd.DataFrame()

    if not st.session_state.logged_in:
        st.markdown("### Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if auth.authenticate(username, password):
                st.session_state.logged_in = True
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid username or password")
    else:
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
                st.session_state.search_results = parallel_search_conversations(df, search_terms)
                if st.session_state.search_results.empty:
                    st.info("No matching conversations found.")
            else:
                st.warning("Please enter search terms to begin.")

        # Display search results and selection buttons
        if not st.session_state.search_results.empty:
            st.markdown(f"### 📊 Search Results: {len(st.session_state.search_results)} unique conversations found")
            for i, (_, row) in enumerate(st.session_state.search_results.iterrows()):
                with st.expander(f"💬 {row['Name of the Profile']} - {row['First Contact Date and Time']}"):
                    st.text_area("Conversation", row['Conversation'], height=200, key=f"conversation_{i}")
                    if row['Conversation'] not in [chat['Conversation'] for chat in st.session_state.selected_chats]:
                        if st.button("Select for download", key=f"select_{i}"):
                            st.session_state.selected_chats.append(row)
                            st.rerun()
                    else:
                        if st.button("Remove from selection", key=f"remove_{i}"):
                            st.session_state.selected_chats = [chat for chat in st.session_state.selected_chats if chat['Conversation'] != row['Conversation']]
                            st.rerun()

        # Download functionality
        if st.session_state.selected_chats:
            st.markdown(f"### Selected Chats: {len(st.session_state.selected_chats)}")
            if st.button("Download Selected Chats"):
                content = download_selected_chats(st.session_state.selected_chats)
                st.download_button(
                    label="Download TXT",
                    data=content,
                    file_name="selected_chats.txt",
                    mime="text/plain",
                    key="download_button"  # Added a key for the download button
                )

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.selected_chats = []
            st.session_state.search_results = pd.DataFrame()
            st.rerun()

if __name__ == "__main__":
    main()