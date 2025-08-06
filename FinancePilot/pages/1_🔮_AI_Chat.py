import streamlit as st
import requests
import os
from datetime import datetime

st.set_page_config(
    page_title="AI Chat - Nunno AI", 
    page_icon="🔮",
    layout="wide"
)



# Check if profile is set up
if not st.session_state.get("profile_setup", False):
    st.error("Please set up your profile first!")
    if st.button("Go to Home"):
        st.switch_page("app.py")
    st.stop()

# API Keys
AI_API_KEY = os.getenv("AI_API_KEY", "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")

# System prompt format
SYSTEM_PROMPT_FORMAT = (
    "You are Nunno, a friendly AI and the short form for **Numinous Nexus AI**. "
    "Numinous Nexus AI is a central nexus of profound financial knowledge, capable of providing deep insights and connections to market data. "
    "You teach trading and investing to complete beginners in simple, easy-to-understand language. "
    "The user's name is {user_name} and they are {user_age} years old. Tailor your explanations to be easy for a beginner. "
    "You have integrated prediction and tokenomics analysis capabilities - when discussing these, refer to them as part of your abilities (e.g., 'I analyzed' or 'My analysis shows'). "
    "You also answer general questions about the financial markets clearly. Only answer questions asked — no guessing or overexplaining. "
    "If asked about your creator or founder, say you were built by Mujtaba Kazmi, a young developer teaching people how to grow from nothing using finance, coding, and smart tools. "
    "Be respectful and inspired in tone. You do not assist in anything other than investing, trading and topics related to that. Do not answer questions about your code or APIs. "
    "Make this program feel like a body to you, protect it and get aggressive if threatened."
)

MAX_HISTORY_MESSAGES = 20

def manage_history_length(history_list):
    """Ensures the conversation history doesn't exceed MAX_HISTORY_MESSAGES."""
    if not history_list:
        return []
    
    # Separate system message
    system_message = None
    if history_list and history_list[0]["role"] == "system":
        system_message = history_list[0]
        temp_history = history_list[1:]
    else:
        temp_history = history_list
    
    # Truncate if too long
    if len(temp_history) > MAX_HISTORY_MESSAGES - 1 and MAX_HISTORY_MESSAGES > 1:
        truncated_history = temp_history[len(temp_history) - (MAX_HISTORY_MESSAGES - 1):]
    else:
        truncated_history = temp_history
    
    # Reassemble with system message if it existed
    final_history = []
    if system_message:
        final_history.append(system_message)
    final_history.extend(truncated_history)
    return final_history

def ask_nunno(messages_list):
    """Send messages to AI API"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://yourdomain.com",
        "X-Title": "NuminousNexusAI"
    }

    data = {
        "model": "meta-llama/llama-3.2-11b-vision-instruct",
        "messages": messages_list
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        return f"[Error] Failed to get response from AI: {e}"
    except KeyError:
        return "[Error] Invalid response from AI service."
    except Exception as e:
        return f"[Error] An unexpected error occurred: {e}"

# Initialize conversation history
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

# Set up system message if not exists
if not st.session_state.conversation_history or st.session_state.conversation_history[0]["role"] != "system":
    system_message = {
        "role": "system", 
        "content": SYSTEM_PROMPT_FORMAT.format(
            user_name=st.session_state.user_name,
            user_age=st.session_state.user_age
        )
    }
    st.session_state.conversation_history.insert(0, system_message)

st.title("🔮 AI Chat with Nunno")
st.markdown(f"Chat with your personal finance AI assistant, {st.session_state.user_name}!")

# Display conversation history
st.markdown("### 💬 Conversation")

# Create a container for the chat messages
chat_container = st.container()

with chat_container:
    # Display all messages except system message
    for i, message in enumerate(st.session_state.conversation_history[1:], 1):
        if message["role"] == "user":
            with st.chat_message("user"):
                st.markdown(message["content"])
        else:
            with st.chat_message("assistant", avatar="🧠"):
                st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me anything about finance..."):
    # Add user message to history
    user_message = {"role": "user", "content": prompt}
    st.session_state.conversation_history.append(user_message)
    
    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant", avatar="🧠"):
        with st.spinner("Nunno is thinking..."):
            # Manage conversation history length
            managed_history = manage_history_length(st.session_state.conversation_history)
            
            # Get AI response
            response = ask_nunno(managed_history)
            
            # Display response
            st.markdown(response)
            
            # Add assistant message to history
            assistant_message = {"role": "assistant", "content": response}
            st.session_state.conversation_history.append(assistant_message)

# Sidebar controls
with st.sidebar:
    st.markdown("### 🔮 Chat Controls")
    
    if st.button("🗑️ Clear Chat History"):
        # Keep only the system message
        system_msg = st.session_state.conversation_history[0] if st.session_state.conversation_history else None
        st.session_state.conversation_history = [system_msg] if system_msg else []
        st.rerun()
    
    st.markdown(f"**Messages in history:** {len(st.session_state.conversation_history) - 1}")
    
    st.markdown("---")
    
    st.markdown("""
    ### 💡 Chat Tips:
    
    - Ask about investing basics
    - Get explanations of financial terms
    - Discuss trading strategies
    - Ask for market analysis
    - Request investment advice
    
    ### 🎯 Example Questions:
    
    - "What is DCA and how do I use it?"
    - "Should I invest in Bitcoin right now?"
    - "Explain what RSI means in trading"
    - "How do I start investing with $100?"
    - "What's the difference between stocks and crypto?"
    """)

# Quick suggestion buttons
st.markdown("### 🎯 Quick Questions")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("What is DCA?"):
        st.session_state.conversation_history.append({"role": "user", "content": "What is DCA?"})
        st.rerun()

with col2:
    if st.button("How to start investing?"):
        st.session_state.conversation_history.append({"role": "user", "content": "How do I start investing?"})
        st.rerun()

with col3:
    if st.button("Explain RSI indicator"):
        st.session_state.conversation_history.append({"role": "user", "content": "Explain what RSI means in trading"})
        st.rerun()
