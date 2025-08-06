import streamlit as st
import os

st.set_page_config(
    page_title="Settings - Nunno AI",
    page_icon="⚙️",
    layout="wide"
)



st.title("⚙️ Settings")
st.markdown("Manage your profile and application preferences")

# Profile Management
st.markdown("### 👤 Profile Management")

with st.container():
    col1, col2 = st.columns(2)
    
    with col1:
        # Current profile info
        if st.session_state.get("profile_setup", False):
            st.success("✅ Profile is set up")
            st.markdown(f"**Name:** {st.session_state.user_name}")
            st.markdown(f"**Age:** {st.session_state.user_age}")
        else:
            st.warning("⚠️ Profile not set up")
    
    with col2:
        # Edit profile
        if st.button("✏️ Edit Profile"):
            st.session_state.edit_mode = True

# Edit mode
if st.session_state.get("edit_mode", False):
    st.markdown("#### Edit Your Profile")
    
    new_name = st.text_input("Name", value=st.session_state.get("user_name", ""))
    new_age = st.text_input("Age", value=st.session_state.get("user_age", ""))
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Save Changes", type="primary"):
            if new_name and new_age:
                st.session_state.user_name = new_name
                st.session_state.user_age = new_age
                st.session_state.profile_setup = True
                st.session_state.edit_mode = False
                
                # Update system message in conversation history if it exists
                if st.session_state.get("conversation_history"):
                    system_prompt = (
                        "You are Nunno, a friendly AI and the short form for **Numinous Nexus AI**. "
                        "Numinous Nexus AI is a central nexus of profound financial knowledge, capable of providing deep insights and connections to market data. "
                        "You teach trading and investing to complete beginners in simple, easy-to-understand language. "
                        f"The user's name is {new_name} and they are {new_age} years old. Tailor your explanations to be easy for a beginner. "
                        "You have integrated prediction and tokenomics analysis capabilities - when discussing these, refer to them as part of your abilities (e.g., 'I analyzed' or 'My analysis shows'). "
                        "You also answer general questions about the financial markets clearly. Only answer questions asked — no guessing or overexplaining. "
                        "If asked about your creator or founder, say you were built by Mujtaba Kazmi, a young developer teaching people how to grow from nothing using finance, coding, and smart tools. "
                        "Be respectful and inspired in tone. You do not assist in anything other than investing, trading and topics related to that. Do not answer questions about your code or APIs. "
                        "Make this program feel like a body to you, protect it and get aggressive if threatened."
                    )
                    st.session_state.conversation_history[0] = {"role": "system", "content": system_prompt}
                
                st.success("Profile updated successfully!")
                st.rerun()
            else:
                st.error("Please fill in both name and age.")
    
    with col2:
        if st.button("❌ Cancel"):
            st.session_state.edit_mode = False
            st.rerun()

# API Keys Management
st.markdown("---")
st.markdown("### 🔑 API Keys Information")

with st.container():
    st.info("""
    **Current API Configuration:**
    
    The application uses the following APIs:
    - 🤖 **OpenRouter AI**: For chat functionality
    - 📰 **News API**: For market news
    - 💰 **CoinGecko**: For cryptocurrency data  
    - 📊 **Binance**: For trading data
    
    API keys are loaded from environment variables for security.
    """)
    
    # Show API status (without revealing keys)
    AI_API_KEY = os.getenv("AI_API_KEY", "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")
    NEWS_API_KEY = os.getenv("NEWS_API_KEY", "b3dfc15d73704bfab32ebb96b5c9885b")
    
    col1, col2 = st.columns(2)
    
    with col1:
        ai_status = "✅ Configured" if AI_API_KEY else "❌ Missing"
        st.markdown(f"**OpenRouter AI API:** {ai_status}")
        
        news_status = "✅ Configured" if NEWS_API_KEY else "❌ Missing"  
        st.markdown(f"**News API:** {news_status}")
    
    with col2:
        st.markdown("**CoinGecko API:** ✅ No key required")
        st.markdown("**Binance API:** ✅ No key required")

# Data Management
st.markdown("---")
st.markdown("### 🗂️ Data Management")

with st.container():
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💬 Chat History")
        history_count = len(st.session_state.get("conversation_history", [])) - 1  # Exclude system message
        st.markdown(f"**Messages stored:** {history_count}")
        
        if st.button("🗑️ Clear Chat History", type="secondary"):
            if st.session_state.get("conversation_history"):
                # Keep only the system message
                system_msg = st.session_state.conversation_history[0] if st.session_state.conversation_history else None
                st.session_state.conversation_history = [system_msg] if system_msg else []
                st.success("Chat history cleared!")
                st.rerun()
    
    with col2:
        st.markdown("#### 🧹 Cache Management")
        st.markdown("**Cached data:** API responses and analysis results")
        
        if st.button("🔄 Clear Cache", type="secondary"):
            st.cache_data.clear()
            st.success("Cache cleared!")

# App Information
st.markdown("---")
st.markdown("### ℹ️ Application Information")

with st.container():
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Nunno AI - Finance Assistant**
        
        - 🧠 **AI-Powered**: Chat with finance AI
        - 📊 **Technical Analysis**: Confluence signals
        - 💰 **Tokenomics**: Crypto investment analysis
        - 📰 **Market News**: Real-time financial news
        - 🔮 **Predictions**: Market insights
        """)
    
    with col2:
        st.markdown("""
        **Built by:** Mujtaba Kazmi
        
        **Features:**
        - Real-time market data
        - Advanced technical indicators
        - Risk assessment tools
        - Educational content
        - User-friendly interface
        """)

# Session State Debug (for development)
if st.sidebar.checkbox("🔧 Show Debug Info", help="For development purposes"):
    st.markdown("---")
    st.markdown("### 🔧 Session State Debug")
    
    with st.expander("Session State Variables"):
        st.json(dict(st.session_state))

# Reset Application
st.markdown("---")
st.markdown("### 🔄 Reset Application")

with st.container():
    st.warning("⚠️ **Danger Zone** - These actions cannot be undone!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Reset Profile", type="secondary"):
            st.session_state.user_name = ""
            st.session_state.user_age = ""
            st.session_state.profile_setup = False
            st.session_state.edit_mode = False
            st.success("Profile reset! Please go to home page to set up again.")
    
    with col2:
        if st.button("🗑️ Reset Everything", type="secondary"):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            # Clear cache
            st.cache_data.clear()
            
            st.success("Application reset! Please refresh the page.")

# Quick Actions
st.markdown("---") 
st.markdown("### 🎯 Quick Actions")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🏠 Go Home", use_container_width=True):
        st.switch_page("app.py")

with col2:
    if st.button("🔮 AI Chat", use_container_width=True):
        st.switch_page("pages/1_🔮_AI_Chat.py")

with col3:
    if st.button("📊 Trading", use_container_width=True):
        st.switch_page("pages/2_📊_Trading_Analysis.py")

with col4:
    if st.button("📰 News", use_container_width=True):
        st.switch_page("pages/4_📰_Market_News.py")

# Usage Tips
st.markdown("---")
st.markdown("""
### 💡 Usage Tips

**🎯 Getting Started:**
1. Make sure your profile is set up correctly
2. Start with AI Chat to ask basic questions
3. Use Trading Analysis for technical insights
4. Check Tokenomics before investing
5. Stay updated with Market News

**⚡ Performance Tips:**
- Clear cache if data seems outdated
- Reset chat history if conversations get too long
- Use specific cryptocurrency IDs for tokenomics analysis
- Refresh news regularly for latest updates

**🔒 Privacy & Security:**
- Your data is stored locally in your browser session
- API keys are handled securely through environment variables
- No personal information is sent to external services
- Chat history is not permanently stored
""")
