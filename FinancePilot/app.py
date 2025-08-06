import streamlit as st
import os
from datetime import datetime

# Configure the page
st.set_page_config(
    page_title="Nunno AI - Finance Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)



# Initialize session state variables
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "user_age" not in st.session_state:
    st.session_state.user_age = ""
if "profile_setup" not in st.session_state:
    st.session_state.profile_setup = False
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

# API Keys from environment variables
AI_API_KEY = os.getenv("AI_API_KEY", "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")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "b3dfc15d73704bfab32ebb96b5c9885b")

def show_welcome():
    """Display welcome screen"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1>🌟✨💫🧠 Welcome to Nunno AI!</h1>
        <h2>💰 Your Personal Finance Assistant</h2>
        <h3>📊 Built by Mujtaba Kazmi</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if not st.session_state.profile_setup:
        st.markdown("### 👤 Let's set up your profile first!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("What's your name?", value=st.session_state.user_name)
        
        with col2:
            age = st.text_input("How old are you?", value=st.session_state.user_age)
        
        if st.button("Save Profile", type="primary"):
            if name and age:
                st.session_state.user_name = name
                st.session_state.user_age = age
                st.session_state.profile_setup = True
                st.success(f"Welcome, {name}! Your profile has been saved.")
                st.rerun()
            else:
                st.error("Please fill in both name and age.")
    else:
        st.success(f"👋 Welcome back, {st.session_state.user_name} ({st.session_state.user_age} years old)!")
        
        if st.button("Edit Profile"):
            st.session_state.profile_setup = False
            st.rerun()

def main():
    # Sidebar
    with st.sidebar:
        st.title("🧠 Nunno AI")
        st.markdown("Your Finance Learning Companion")
        
        if st.session_state.profile_setup:
            st.markdown(f"👤 **{st.session_state.user_name}** ({st.session_state.user_age})")
        
        st.markdown("---")
        
        st.markdown("""
        ### 🚀 What I can help you with:
        
        - 🔮 **AI Chat**: Ask me anything about finance
        - 📊 **Trading Analysis**: Technical analysis with confluences
        - 💰 **Tokenomics**: Analyze cryptocurrency investments
        - 📰 **Market News**: Latest financial news
        - ⚙️ **Settings**: Manage your profile and preferences
        """)
        
        st.markdown("---")
        
        st.markdown("""
        ### 💡 Quick Tips:
        - Ask me naturally in plain English
        - I can analyze any cryptocurrency
        - Try "Analyze Bitcoin" or "Should I invest in Ethereum?"
        - Check market news for the latest updates
        """)

    # Main content
    if not st.session_state.profile_setup:
        show_welcome()
    else:
        st.markdown(f"""
        # 🎉 Welcome to Nunno AI, {st.session_state.user_name}!
        
        I'm here to help you learn investing and trading in simple terms.
        
        ### 🚀 Choose what you'd like to do:
        
        Use the sidebar navigation to explore different features:
        
        - **🔮 AI Chat**: Have a conversation with me about finance
        - **📊 Trading Analysis**: Get technical analysis with confluence signals  
        - **💰 Tokenomics**: Analyze cryptocurrency investments
        - **📰 Market News**: Stay updated with latest market news
        - **⚙️ Settings**: Manage your profile and preferences
        
        ### 💡 Getting Started:
        
        1. **New to trading?** Start with the AI Chat to ask basic questions
        2. **Want to analyze a coin?** Use the Tokenomics page
        3. **Looking for signals?** Check out Trading Analysis
        4. **Stay informed?** Visit Market News for latest updates
        
        Select a page from the sidebar to get started! 👈
        """)
        
        # Quick action buttons
        st.markdown("### 🎯 Quick Actions:")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔮 Start AI Chat", use_container_width=True):
                st.switch_page("pages/1_🔮_AI_Chat.py")
        
        with col2:
            if st.button("📊 Trading Analysis", use_container_width=True):
                st.switch_page("pages/2_📊_Trading_Analysis.py")
        
        with col3:
            if st.button("💰 Tokenomics", use_container_width=True):
                st.switch_page("pages/3_💰_Tokenomics.py")
        
        with col4:
            if st.button("📰 Market News", use_container_width=True):
                st.switch_page("pages/4_📰_Market_News.py")

if __name__ == "__main__":
    main()
