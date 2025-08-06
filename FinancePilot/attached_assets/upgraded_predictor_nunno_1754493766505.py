import requests
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
from datetime import datetime
import betterpredictormodule
import numpy as np
from fuzzywuzzy import process
import time
import re # Added for better prompt parsing

import pyttsx3
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 175)
tts_engine.setProperty('volume', 1.0)

dark_mode_enabled = False


# === API KEYS ===
# IMPORTANT: For security, consider loading API keys from environment variables
# or a configuration file, ratherarding them directly in the script.
AI_API_KEY = "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"
NEWS_API_KEY = "b3dfc15d73704bfab32ebb96b5c9885b"


# === Globals ===
current_thread = None # Stores the currently running background thread
stop_flag = False     # Flag to signal threads to stop gracefully
welcome_shown = False # Flag to ensure welcome animation plays only once

# --- User Profile Globals ---
user_name = "User" # Default name
user_age = "N/A"   # Default age

# --- Conversation History ---
conversation_history = []

# This will be a format string, filled in after user enters name/age
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

# Limit conversation history to manage token count and focus on recent context
# Phi-3 Mini has 128k context, so 20-30 turns is usually fine.
MAX_HISTORY_MESSAGES = 20 # 10 user questions + 10 Nunno answers, plus system prompt

def manage_history_length(history_list):
    """
    Ensures the conversation history doesn't exceed MAX_HISTORY_MESSAGES.
    Keeps the system message at the beginning.
    """
    if not history_list:
        return []
    
    # Separate system message
    system_message = None
    if history_list and history_list[0]["role"] == "system":
        system_message = history_list[0]
        temp_history = history_list[1:] # History without system message
    else:
        temp_history = history_list # No system message at the start

    # Truncate if too long (keep MAX_HISTORY_MESSAGES - 1 for actual turns)
    # Ensure at least one element for non-system messages
    if len(temp_history) > MAX_HISTORY_MESSAGES -1 and MAX_HISTORY_MESSAGES > 1:
        truncated_history = temp_history[len(temp_history) - (MAX_HISTORY_MESSAGES -1):]
    else:
        truncated_history = temp_history
    
    # Reassemble with system message if it existed
    final_history = []
    if system_message:
        final_history.append(system_message)
    final_history.extend(truncated_history)
    return final_history


# --- Tokenomics Functions ---
# (No changes needed in these core logic functions for the UI issue)

def fetch_historical_prices(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=365"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        return [p[1] for p in data["prices"]]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching historical prices for {coin_id}: {e}")
        return None

def calculate_cagr_and_volatility(prices):
    try:
        returns = [np.log(prices[i+1] / prices[i]) for i in range(len(prices)-1)]
        if not returns: # Handle case with insufficient data for returns
            return None, None, None
        avg_daily_return = np.mean(returns)
        daily_volatility = np.std(returns)
        trading_days = 365
        annual_return = np.exp(avg_daily_return * trading_days) - 1
        annual_volatility = daily_volatility * np.sqrt(trading_days)
        conservative_return = annual_return * 0.5
        return annual_return, annual_volatility, conservative_return
    except Exception as e:
        print(f"Error calculating CAGR and Volatility: {e}")
        return None, None, None

def suggest_similar_tokens(user_input):
    try:
        res = requests.get("https://api.coingecko.com/api/v3/coins/list")
        res.raise_for_status()
        coin_list = res.json()
        coin_ids = [coin['id'] for coin in coin_list]
        best_matches = process.extract(user_input.lower(), coin_ids, limit=5)
        return [match[0] for match in best_matches if match[1] > 60]
    except requests.exceptions.RequestException as e:
        print(f"Error suggesting similar tokens: {e}")
        return []

def fetch_token_data(coin_id, investment_amount=1000):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id.lower().strip()}"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        market = data["market_data"]

        circulating = market.get("circulating_supply", 0)
        total = market.get("total_supply", 0)
        price = market.get("current_price", {}).get("usd", 0)
        mcap = market.get("market_cap", {}).get("usd", 0)
        
        fdv = total * price if total else 0
        circ_percent = (circulating / total) * 100 if total else None
        fdv_mcap_ratio = (fdv / mcap) if mcap and mcap != 0 else None # Avoid division by zero

        healthy = "✅ This coin seems healthy!" if circ_percent and circ_percent > 50 and fdv_mcap_ratio and fdv_mcap_ratio < 2 else "⚠️ Warning: This coin might be risky or inflated."

        prices = fetch_historical_prices(coin_id)
        if not prices or len(prices) < 2: # Need at least 2 prices for returns
            cagr, volatility, conservative_cagr = None, None, None
        else:
            cagr, volatility, conservative_cagr = calculate_cagr_and_volatility(prices)

        expected_yearly_return = investment_amount * conservative_cagr if conservative_cagr is not None else 0
        expected_monthly_return = expected_yearly_return / 12

        return {
            "Coin Name & Symbol": f"{data['name']} ({data['symbol'].upper()})",
            "Current Price ($)": f"${price:,.6f}",
            "Market Cap (B)": f"${mcap / 1e9:,.2f}B — The value of all coins in the market",
            "Total Supply (M)": f"{total / 1e6:,.2f}M — Maximum possible number of coins",
            "Circulating Supply (M)": f"{circulating / 1e6:,.2f}M — Coins that are currently in circulation",
            "Circulating Supply %": f"{circ_percent:,.2f}%" if circ_percent is not None else "N/A",
            "FDV (B)": f"${fdv / 1e9:,.2f}B — What the coin could be worth if all coins were unlocked",
            "FDV/Market Cap Ratio": f"{fdv_mcap_ratio:,.2f} — The lower this ratio, the better" if fdv_mcap_ratio is not None else "N/A",
            "Historical Annual Return (CAGR)": f"{cagr * 100:,.2f}% — How much the coin has grown in a year" if cagr is not None else "N/A",
            "Annual Volatility": f"{volatility * 100:,.2f}% — Price fluctuation level" if volatility is not None else "N/A",
            "Realistic Yearly Return (50% CAGR)": f"{conservative_cagr * 100:,.2f}%" if conservative_cagr is not None else "N/A",
            "Expected Monthly Return ($)": f"${expected_monthly_return:,.2f}" if expected_monthly_return is not None else "N/A",
            "Expected Yearly Return ($)": f"${expected_yearly_return:,.2f}" if expected_yearly_return is not None else "N/A",
            "Should I Invest?": healthy
        }
    except requests.exceptions.RequestException as e:
        print(f"Error fetching token data for {coin_id}: {e}")
        return None

# --- Fetch Market News ---
def fetch_market_news():
    url = "https://newsapi.org/v2/everything"
    today = datetime.now().strftime("%Y-%m-%d")
    params = {
        "q": "finance OR stock market OR bitcoin OR federal reserve OR inflation OR interest rates",
        "from": today,
        "sortBy": "publishedAt",
        "language": "en",
        "apiKey": NEWS_API_KEY,
        "pageSize": 5,
        "domains": "cnbc.com, bloomberg.com, reuters.com, wsj.com"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        headlines = [f"- {a['title']} ({a['source']['name']})" for a in articles]
        return "\n".join(headlines)
    except Exception as e:
        print(f"Error fetching market news: {e}")
        return None

# --- Ask Nunno (AI Chat Completion) ---
# Modified to accept a list of messages for conversation history
def ask_nunno(messages_list):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://yourdomain.com", # Replace with your actual domain for OpenRouter
        "X-Title": "NuminousNexusAI" # Your application title for OpenRouter
    }

    data = {
        "model": "meta-llama/llama-3.2-11b-vision-instruct", # Changed model
        "messages": messages_list # Now uses the full list of messages
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return f"[Error] Failed to get response from AI: {e}"
    except KeyError:
        print("API response did not contain expected 'choices' or 'message' key.")
        return "[Error] Invalid response from AI service."
    except Exception as e:
        print(f"An unexpected error occurred in ask_nunno: {e}")
        return f"[Error] An unexpected error occurred: {e}"

# --- Typing Effect ---
def display_typing_effect(text, tag):
    global stop_flag
    for char in text:
        if stop_flag:
            break # Exit the loop if stop_flag is set
        chat_log.insert(tk.END, char, tag)
        chat_log.see(tk.END)
        chat_log.update_idletasks() # Update the UI immediately
        time.sleep(0.015) # Shorter delay for smoother typing

# --- Welcome Animation ---
def show_welcome_animation():
    global welcome_shown
    if welcome_shown:
        return
    welcome_shown = True
    
    chat_log.delete(1.0, tk.END) # Clear chat log for animation
    
    # Animation frames
    frames = [
        "🌟",
        "🌟✨",
        "🌟✨💫",
        "🌟✨💫🧠",
        "🌟✨💫🧠 Welcome to Nunno!",
        "🌟✨💫🧠 Welcome to Nunno!\n\n💰 Your Personal Finance Assistant",
        "🌟✨💫🧠 Welcome to Nunno!\n\n💰 Your Personal Finance Assistant\n📊 Built by Mujtaba Kazmi"
    ]
    
    for i, frame in enumerate(frames):
        if i > 0:
            chat_log.delete(1.0, tk.END)
        chat_log.insert(tk.END, frame, "welcome_anim")
        chat_log.see(tk.END)
        chat_log.update_idletasks()
        time.sleep(0.8)
    
    time.sleep(1)
    chat_log.delete(1.0, tk.END)
    
    # Use personalized welcome message
    welcome_msg = f"""🎉 Welcome to Nunno AI, {user_name} - Your Finance Learning Companion!

I'm here to help you learn investing and trading in simple terms.

🚀 What I can help you with:

📊 ANALYZE COINS: "Analyze Bitcoin" or "Should I invest $1000 in Ethereum?"
🔮 PREDICTIONS: "What's Bitcoin's next move?" or "Predict SOL price"
📰 MARKET NEWS: "What's happening in the market today?"
🧪 TEST STRATEGIES: "Simulate 70% win rate with 2:1 risk-reward"
📚 LEARN: "What is DCA?" or "How do I start investing?"

💡 Tip: Just ask me naturally! I understand plain English.

Type your question below and press Enter or click Ask! 👇"""

    chat_log.insert(tk.END, welcome_msg, "welcome")
    chat_log.see(tk.END)
    
    add_example_buttons() # Add some example buttons

# --- Example Buttons ---
def add_example_buttons():
    # Clear existing example buttons if any
    for widget in examples_container.winfo_children():
        widget.destroy()

    examples_frame = tk.Frame(examples_container, bg="#f8f9fa", relief="flat", bd=0)
    examples_frame.pack(fill=tk.X, pady=5)
    
    examples = [
        ("📊 Analyze Bitcoin", "Analyze Bitcoin with $1000"),
        ("📰 Market News", "What's happening in the market?"),
        ("🔮 Predict BTC", "What's Bitcoin's next move?"),
        ("📚 Learn DCA", "What is dollar cost averaging?")
    ]
    
    # Re-add title for examples
    examples_title = tk.Label(
        examples_frame, text="💡 Quick Start Examples:", font=("Segoe UI", 10, "bold"), bg="#f8f9fa", fg="#666666"
    )
    examples_title.pack(anchor="w", padx=15, pady=(10, 5))

    for text, command in examples:
        btn = tk.Button(
            examples_frame,
            text=text,
            command=lambda cmd=command: example_clicked(cmd),
            bg="#e3f2fd",
            fg="#1976d2",
            font=("Segoe UI", 9),
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2"
        )
        btn.pack(side=tk.LEFT, padx=5, pady=2)
        
        # Hover effects - Renamed to avoid clash with main on_enter
        def on_enter_hover(e, button=btn):
            button.config(bg="#bbdefb")
        def on_leave_hover(e, button=btn):
            button.config(bg="#e3f2fd")
            
        btn.bind("<Enter>", on_enter_hover)
        btn.bind("<Leave>", on_leave_hover)

def example_clicked(command):
    entry.delete(0, tk.END)
    entry.insert(0, command)
    on_enter()


import base64
from tkinter import filedialog

def encode_image(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"❌ Error reading image: {e}")
        return None

def analyze_chart(image_b64):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "meta-llama/llama-3.2-11b-vision-instruct", # Changed model
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "You're an expert trading analyst. Analyze this chart, identify trend, support/resistance, patterns, and predict the next move."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
            ]
        }],
        "max_tokens": 1000
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ API error: {e}"

def chart_analysis_thread():
    global stop_flag, conversation_history
    stop_flag = False
    disable_input_controls()
    status_label.config(text="📷 Analyzing chart...", fg="#FF6F00")

    image_path = filedialog.askopenfilename(
        title="Select Chart Image",
        filetypes=[("Image Files", "*.png *.jpg *.jpeg")]
    )
    if not image_path:
        enable_input_controls()
        return

    chat_log.insert(tk.END, f"\n📷 You uploaded: {image_path.split('/')[-1]}\n", "user")
    image_b64 = encode_image(image_path)
    if not image_b64:
        chat_log.insert(tk.END, "❌ Could not read the image.\n", "error")
        enable_input_controls()
        return

    analysis = analyze_chart(image_b64)
    chat_log.insert(tk.END, "📈 Chart Analysis Result:\n", "analysis_header")
    chat_log.insert(tk.END, analysis + "\n", "nunno")

    conversation_history.append({"role": "user", "content": "Here is a chart analysis result:\n" + analysis + "\nPlease explain what this means for a beginner trader."})
    response = ask_nunno(conversation_history)
    conversation_history.append({"role": "assistant", "content": response})
    chat_log.insert(tk.END, "🧠 Nunno's Commentary:\n", "nunno_header")
    display_typing_effect(response + "\n", "nunno")

    enable_input_controls()


# --- UI Control Functions ---
def enable_input_controls():
    """Enable input controls and reset status. Call from main thread."""
    root.after(0, lambda: [
        entry.config(state="normal"),
        ask_btn.config(state="normal", text="Ask Nunno"),
        stop_btn.config(state="disabled"), # Disable stop button when ready
        status_label.config(text="✅ Ready to help!", fg="#4caf50")
    ])

def disable_input_controls():
    """Disable input controls during processing. Call from main thread."""
    root.after(0, lambda: [ # Ensure this runs on the main thread
        entry.config(state="disabled"),
        ask_btn.config(state="disabled", text="Processing..."),
        stop_btn.config(state="normal") # Enable stop button when processing
    ])

# --- Stop Function ---
def stop_response():
    global stop_flag, current_thread
    stop_flag = True # Signal the running thread to stop
    
    chat_log.insert(tk.END, "\n🛑 Response stopped by user.\n", "error")
    chat_log.see(tk.END)

    # Immediately re-enable input controls
    enable_input_controls() 
    
    # Attempt to join the thread briefly to allow it to finish gracefully
    # This is non-blocking to the UI due to the short timeout
    if current_thread and current_thread.is_alive():
        current_thread.join(timeout=0.1)

# --- Clear History / New Chat Function ---
def new_chat():
    global conversation_history, welcome_shown
    chat_log.delete(1.0, tk.END)
    
    # Reset conversation history with the dynamic system prompt
    global user_name, user_age
    formatted_system_prompt = SYSTEM_PROMPT_FORMAT.format(user_name=user_name, user_age=user_age)
    conversation_history = [{"role": "system", "content": formatted_system_prompt}]
    
    welcome_shown = False # Allow welcome animation to play again
    show_welcome_animation() # Re-show welcome message and examples
    enable_input_controls()
    status_label.config(text="✅ New chat started!", fg="#4caf50")


# --- Handle Question (Main Logic Dispatcher) ---
def handle_question(prompt):
    global stop_flag, current_thread, conversation_history
    stop_flag = False # Reset the stop flag for the new question

    # Lock input during response
    disable_input_controls()
    
    # Update status
    status_label.config(text="🤔 Nunno is thinking...", fg="#FFA000") # Brighter orange/amber

    chat_log.insert(tk.END, "\n" + "─" * 50 + "\n", "separator")
    chat_log.update()

    # Append user's current message to history BEFORE dispatching to threads
    conversation_history.append({"role": "user", "content": prompt})
    
    # Keywords for different functionalities
    news_keywords = [
        "explain news", "what's happening in the market", "market news", "latest headlines",
        "tell me the news", "financial news", "business news", "what's the news", "latest market update",
        "explain market headlines", "summarize the news", "what's going on in finance", "economy update"
    ]

    prediction_keywords = [
        "next move", "price prediction", "where will", "what's next for", "forecast", "predict", "prediction"
    ]

    montecarlo_keywords = ["simulate", "monte carlo", "simulate strategy", "test my rules"]
    
    tokenomics_keywords = [
        "tokenomics", "supply", "circulating supply", "max supply", "inflation rate", "coin info",
        "analyze", "token analysis", "investment analysis", "should i invest", "coin data",
        "fdv", "market cap", "fully diluted", "volatility", "cagr"
    ]

    # --- Prediction Thread ---
    def prediction_thread_func():
        global stop_flag, conversation_history # Access global history
        try:
            status_label.config(text="🔮 Running prediction algorithm...", fg="#E040FB") # Brighter purple/magenta
            if stop_flag: return
            
            detected_token = "BTCUSDT"
            for token in ["BTC", "ETH", "SOL", "DOGE", "BNB", "MATIC", "AVAX"]:
                if token.lower() in prompt.lower():
                    detected_token = token.upper() + "USDT"
                    break

            detected_tf = "15m"
            for tf in {"1m", "5m", "15m", "1h", "4h"}:
                if tf in prompt:
                    detected_tf = tf
                    break

            if stop_flag: return

            analyzer = betterpredictormodule.TradingAnalyzer()
            try:
                df = analyzer.fetch_binance_ohlcv(symbol=detected_token, interval=detected_tf, limit=1000)
            except Exception as e:
                error_msg = f"❌ Could not fetch data for {detected_token}: {e}\n"
                chat_log.insert(tk.END, error_msg, "error")
                conversation_history.append({"role": "assistant", "content": error_msg})
                return
            if stop_flag: return
            if df is None or df.empty:
                error_msg = f"❌ Could not fetch data for {detected_token}. Please try again later.\n"
                chat_log.insert(tk.END, error_msg, "error")
                conversation_history.append({"role": "assistant", "content": error_msg})
                return

            df = analyzer.add_comprehensive_indicators(df)
            if stop_flag: return
            if df is None or df.empty:
                error_msg = f"❌ Could not compute indicators for {detected_token}.\n"
                chat_log.insert(tk.END, error_msg, "error")
                conversation_history.append({"role": "assistant", "content": error_msg})
                return

            confluences, latest_row = analyzer.generate_comprehensive_analysis(df)
            bias, strength = analyzer.calculate_confluence_strength(confluences)

            # Prepare summary for chat log
            summary = (
                f"🎯 CONFLUENCE ANALYSIS RESULT\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Symbol: {detected_token} ({detected_tf})\n"
                f"Bias: {bias} ({strength:.1f}% confidence)\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
            )
            if not stop_flag:
                chat_log.insert(tk.END, summary, "prediction_result")
                # Add the confluence result itself to the history so AI can refer to it
                conversation_history.append({
                    "role": "assistant",
                    "content": f"Confluence analysis for {detected_token} ({detected_tf}): Bias is {bias} ({strength:.1f}% confidence)."
                })

                # Display detailed confluences
                def format_confluences(confs, label):
                    if not confs:
                        return ""
                    text = f"{label} ({len(confs)} signals):\n"
                    for i, conf in enumerate(confs, 1):
                        text += f"{i}. {conf['indicator']} [{conf['strength']}] - {conf['timeframe']}\n"
                        text += f"   📍 Condition: {conf['condition']}\n"
                        text += f"   💡 Implication: {conf['implication']}\n"
                    return text + "\n"
                chat_log.insert(tk.END, format_confluences(confluences['bullish'], "🟢 BULLISH CONFLUENCES"), "nunno")
                chat_log.insert(tk.END, format_confluences(confluences['bearish'], "🔴 BEARISH CONFLUENCES"), "nunno")
                chat_log.insert(tk.END, format_confluences(confluences['neutral'], "🟡 NEUTRAL/MIXED SIGNALS"), "nunno")

                # Display trading plan
                chat_log.insert(tk.END, "\n📋 TRADING PLAN SUGGESTIONS:\n", "nunno_header")
                import io
                import sys
                old_stdout = sys.stdout
                sys.stdout = mystdout = io.StringIO()
                betterpredictormodule.generate_trading_plan(confluences, latest_row, bias, strength)
                sys.stdout = old_stdout
                plan_text = mystdout.getvalue()
                chat_log.insert(tk.END, plan_text + "\n", "nunno")

                # Add the trading plan to the conversation history for AI context
                conversation_history.append({
                    "role": "assistant",
                    "content": f"Trading plan for {detected_token} ({detected_tf}):\n{plan_text}"
                })

                # Now, ask Nunno to explain the full context, including the new analysis result
                explanation_prompt_content = f"Based on the confluence analysis and trading plan for {detected_token}, can you break this down simply for a beginner and explain what it means for my trading?"
                messages_for_api = manage_history_length(list(conversation_history))
                messages_for_api.append({"role": "user", "content": explanation_prompt_content})
                response = ask_nunno(messages_for_api)
                if not stop_flag:
                    conversation_history.append({"role": "assistant", "content": response})
                    chat_log.insert(tk.END, "🧠 Nunno's Analysis:\n", "nunno_header")
                    display_typing_effect(response + "\n", "nunno")
        except Exception as e:
            if not stop_flag:
                error_msg = f"❌ Prediction Error: {e}\n"
                chat_log.insert(tk.END, error_msg, "error")
                print(f"Prediction Thread Error: {e}")
                conversation_history.append({"role": "assistant", "content": f"An error occurred during prediction: {e}"})
        finally:
            enable_input_controls()

    # --- Tokenomics Thread ---
    def tokenomics_thread_func():
        global stop_flag, conversation_history
        try:
            status_label.config(text="📊 Analyzing tokenomics...", fg="#42A5F5") # Brighter blue
            if stop_flag: return
            
            coin_mappings = {
                'bitcoin': 'bitcoin', 'btc': 'bitcoin', 'ethereum': 'ethereum', 'eth': 'ethereum',
                'solana': 'solana', 'sol': 'solana', 'cardano': 'cardano', 'ada': 'cardano',
                'polygon': 'matic-network', 'matic': 'matic-network', 'chainlink': 'chainlink', 'link': 'chainlink',
                'dogecoin': 'dogecoin', 'doge': 'dogecoin', 'avalanche': 'avalanche-2', 'avax': 'avalanche-2',
                'polkadot': 'polkadot', 'dot': 'polkadot', 'binance': 'binancecoin', 'bnb': 'binancecoin'
            }
            
            detected_coin = None
            investment_amount = 1000
            
            prompt_lower = prompt.lower()
            for key, value in coin_mappings.items():
                if key in prompt_lower:
                    detected_coin = value
                    break
            
            amount_match = re.search(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', prompt)
            if amount_match:
                investment_amount = float(amount_match.group(1).replace(',', ''))
            
            if not detected_coin:
                # Fallback: if no direct match, try to extract a word that looks like a coin
                words = prompt_lower.replace('?', '').replace(',', '').split()
                # Filter out common stop words and short words
                filtered_words = [word for word in words if len(word) > 2 and word not in ['the', 'and', 'should', 'invest', 'analyze', 'what', 'how', 'when', 'where', 'in', 'a', 'of', 'my', 'is', 'for', 'me']]
                
                # Check for two-word coin names that might be missed (e.g., "terra luna")
                # This is a very basic attempt and could be improved with a more robust coin name recognition
                for i in range(len(words) - 1):
                    two_word_phrase = f"{words[i]} {words[i+1]}"
                    if two_word_phrase in coin_mappings:
                        detected_coin = coin_mappings[two_word_phrase]
                        break
                
                if not detected_coin and filtered_words:
                    detected_coin = filtered_words[0] # Just take the first meaningful word

            if stop_flag: return
            
            if not detected_coin:
                if not stop_flag:
                    nunno_msg = "I'd love to analyze a coin for you! Please specify which coin you'd like me to analyze (e.g., Bitcoin, Ethereum, Solana).\n"
                    chat_log.insert(tk.END, "🧠 Nunno:\n", "nunno_header")
                    display_typing_effect(nunno_msg, "nunno")
                    conversation_history.append({"role": "assistant", "content": nunno_msg}) # Add to history
                return
            
            token_data = fetch_token_data(detected_coin, investment_amount)
            
            if stop_flag: return
            
            if not token_data:
                suggestions = suggest_similar_tokens(detected_coin)
                suggestion_text = ""
                if suggestions and not stop_flag:
                    suggestion_text = f"I couldn't find '{detected_coin}'. Did you mean one of these?\n" + "\n".join([f"• {s}" for s in suggestions[:3]]) + "\n"
                elif not stop_flag:
                    suggestion_text = f"I couldn't find data for '{detected_coin}'. Please check the spelling or try a different coin.\n"
                
                chat_log.insert(tk.END, "🧠 Nunno:\n", "nunno_header")
                display_typing_effect(suggestion_text, "nunno")
                conversation_history.append({"role": "assistant", "content": suggestion_text}) # Add to history
                return
            
            if stop_flag: return
            
            if not stop_flag:
                chat_log.insert(tk.END, "📈 TOKENOMICS ANALYSIS\n", "analysis_header")
                chat_log.insert(tk.END, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", "separator")
                
                formatted_token_data_for_ai = "" # For AI context
                for key, value in token_data.items():
                    if stop_flag: return
                    chat_log.insert(tk.END, f"• {key}: ", "token_key")
                    chat_log.insert(tk.END, f"{value}\n", "token_value")
                    formatted_token_data_for_ai += f"• {key}: {value}\n" # Build string for AI
                
                chat_log.insert(tk.END, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n", "separator")
                
                # Add the detailed token data to history for AI's context
                conversation_history.append({
                    "role": "assistant", # Using assistant role for this factual output
                    "content": f"Here is the detailed tokenomics analysis for {token_data['Coin Name & Symbol']}:\n{formatted_token_data_for_ai}"
                })
            
            if stop_flag: return
            
            # Now, ask Nunno to explain this data
            explanation_prompt_content = f"Based on the tokenomics data above for {token_data['Coin Name & Symbol']}, what does this mean for a beginner investor, and should I consider investing {investment_amount}? Give me a clear and concise summary."
            
            messages_for_api = manage_history_length(list(conversation_history)) # Get truncated history
            messages_for_api.append({"role": "user", "content": explanation_prompt_content})

            response = ask_nunno(messages_for_api)
            if not stop_flag:
                conversation_history.append({"role": "assistant", "content": response}) # Add Nunno's explanation to history
                chat_log.insert(tk.END, "🧠 Nunno's Analysis:\n", "nunno_header")
                display_typing_effect(response + "\n", "nunno")
                
        except Exception as e:
            if not stop_flag:
                error_msg = f"❌ Tokenomics Analysis Error: {e}\n"
                chat_log.insert(tk.END, error_msg, "error")
                print(f"Tokenomics Thread Error: {e}") # Log error for debugging
                conversation_history.append({"role": "assistant", "content": f"An error occurred during tokenomics analysis: {e}"}) # Add error to history
        finally:
            enable_input_controls()

    # --- Monte Carlo Simulation Thread ---
    def montecarlo_thread_func():
        global stop_flag, conversation_history
        try:
            status_label.config(text="🧪 Running Monte Carlo simulation...", fg="#F44336") # Vibrant red
            if stop_flag: return
            
            from montecarlo_module import simulate_trades, monte_carlo_summary # Assuming this module exists
            
            if stop_flag: return
            
            win_rate_match = re.search(r'(\d+(\.\d+)?)\s*%?\s*win\s*rate', prompt.lower())
            rr_ratio_match = re.search(r'(\d+(\.\d+)?)\s*(rr|r:r|risk:?reward)', prompt.lower())
            num_trades_match = re.search(r'(\d+)\s*(trades|trading sessions)', prompt.lower())
            market_match = re.search(r'(trending|bullish|bearish|choppy|sideways)', prompt.lower())

            win_rate = float(win_rate_match.group(1)) / 100 if win_rate_match else 0.5
            rr_ratio = float(rr_ratio_match.group(1)) if rr_ratio_match else 1.5
            num_trades = int(num_trades_match.group(1)) if num_trades_match else 100
            market_condition = market_match.group(1) if market_match else "choppy"

            if stop_flag: return

            result = simulate_trades(win_rate, rr_ratio, num_trades, market_condition)
            summary = monte_carlo_summary(result)

            if not stop_flag:
                chat_log.insert(tk.END, "🧪 MONTE CARLO SIMULATION\n", "simulation_header")
                chat_log.insert(tk.END, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", "separator")
                chat_log.insert(tk.END, summary + "\n", "simulation_result")
                chat_log.insert(tk.END, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n", "separator")
                
                # Add the simulation summary to history
                conversation_history.append({
                    "role": "assistant", # Using assistant role for this factual output
                    "content": f"Monte Carlo Simulation Results:\n{summary}\n"
                })

                # Now, ask Nunno for an explanation or next steps
                explanation_prompt_content = "Based on these Monte Carlo simulation results, what are the key takeaways for a beginner, and what should I consider next?"
                
                messages_for_api = manage_history_length(list(conversation_history)) # Get truncated history
                messages_for_api.append({"role": "user", "content": explanation_prompt_content})

                response = ask_nunno(messages_for_api)
                if not stop_flag:
                    conversation_history.append({"role": "assistant", "content": response}) # Add Nunno's explanation to history
                    chat_log.insert(tk.END, "🧠 Nunno's Analysis:\n", "nunno_header")
                    display_typing_effect(response + "\n", "nunno")

        except Exception as e:
            if not stop_flag:
                error_msg = f"❌ Error in Monte Carlo simulation: {e}\n"
                chat_log.insert(tk.END, error_msg, "error")
                display_typing_effect("Please try something like:\n'Simulate with 60% win rate, 2R:R, in trending market.'\n", "nunno")
                print(f"Monte Carlo Thread Error: {e}") # Log error for debugging
                conversation_history.append({"role": "assistant", "content": f"An error occurred during Monte Carlo simulation: {e}. Please try a valid format like 'Simulate 60% win rate, 2R:R'."}) # Add error to history
        finally:
            enable_input_controls()

    # --- News Request Thread ---
    def ask_news_thread_func():
        global stop_flag, conversation_history
        try:
            status_label.config(text="📰 Fetching latest market news...", fg="#00BCD4") # Teal
            if stop_flag: return
            
            news_text = fetch_market_news()
            if not news_text:
                if not stop_flag:
                    nunno_msg = "Couldn't fetch news at the moment. Please try again later.\n"
                    chat_log.insert(tk.END, f"🧠 Nunno:\n{nunno_msg}", "nunno_header")
                    conversation_history.append({"role": "assistant", "content": nunno_msg}) # Add to history
                return
                
            if stop_flag: return
                
            # Add news headlines to history
            conversation_history.append({
                "role": "assistant", # Using assistant role for factual data
                "content": f"Here are the latest financial news headlines:\n\n{news_text}"
            })
            
            # Now ask Nunno to explain the headlines in the full conversation context
            explanation_prompt_content = "Please explain these news headlines in simple language for a beginner, focusing on their potential market impact."
            
            messages_for_api = manage_history_length(list(conversation_history)) # Get truncated history
            messages_for_api.append({"role": "user", "content": explanation_prompt_content})

            response = ask_nunno(messages_for_api)
            if not stop_flag:
                conversation_history.append({"role": "assistant", "content": response}) # Add Nunno's explanation to history
                chat_log.insert(tk.END, "🧠 Nunno:\n", "nunno_header")
                display_typing_effect(response + "\n", "nunno")
        except Exception as e:
            if not stop_flag:
                error_msg = f"❌ Error fetching news: {e}\n"
                chat_log.insert(tk.END, error_msg, "error")
                print(f"News Thread Error: {e}") # Log error for debugging
                conversation_history.append({"role": "assistant", "content": f"An error occurred while fetching news: {e}"}) # Add error to history
        finally:
            enable_input_controls()

    # --- General Question Thread ---
    def ask_normal_thread_func():
        global stop_flag, conversation_history
        try:
            status_label.config(text="🧠 Nunno is analyzing your question...", fg="#2196F3") # Bright blue
            
            # Pass the accumulated and managed history directly to ask_nunno
            messages_for_api = manage_history_length(list(conversation_history))
            response = ask_nunno(messages_for_api)
            
            if not stop_flag:
                conversation_history.append({"role": "assistant", "content": response}) # Add Nunno's response to history
                chat_log.insert(tk.END, "🧠 Nunno:\n", "nunno_header")
                display_typing_effect(response + "\n", "nunno")
        except Exception as e:
            error_msg = f"❌ Error: {e}\n"
            chat_log.insert(tk.END, error_msg, "error")
            print(f"Normal Thread Error: {e}") # Log error for debugging
            conversation_history.append({"role": "assistant", "content": f"An unexpected error occurred: {e}"}) # Add error to history
        finally:
            enable_input_controls()

    # Determine which thread to run based on user prompt
    if any(keyword in prompt.lower() for keyword in prediction_keywords):
        current_thread = threading.Thread(target=prediction_thread_func)
    elif any(keyword in prompt.lower() for keyword in tokenomics_keywords):
        current_thread = threading.Thread(target=tokenomics_thread_func)
    elif any(keyword in prompt.lower() for keyword in montecarlo_keywords):
        current_thread = threading.Thread(target=montecarlo_thread_func)
    elif any(keyword in prompt.lower() for keyword in news_keywords):
        current_thread = threading.Thread(target=ask_news_thread_func)
    else:
        current_thread = threading.Thread(target=ask_normal_thread_func)

    current_thread.start()

# === GUI Setup ===
root = tk.Tk()
root.title("🧠 Numinous Nexus AI") # Updated title
root.geometry("900x800")
root.configure(bg="#f5f5f5")
root.minsize(800, 600)

# Set window icon (if you have an icon file)
try:
    root.iconbitmap("nunno_icon.ico")
except:
    pass # Handle case where icon file is not found

# --- Main Application Frame (holds all chat UI) ---
main_app_frame = tk.Frame(root, bg="#f5f5f5")
# This frame will be packed/unpacked

# --- Header Frame (inside main_app_frame) ---
header_frame = tk.Frame(main_app_frame, bg="#1976d2", height=80)
header_frame.pack(fill=tk.X)
header_frame.pack_propagate(False)

title_label = tk.Label(
    header_frame, text="🧠 Nunno", font=("Segoe UI", 20, "bold"), bg="#1976d2", fg="white" # Use short name here
)
title_label.pack(side=tk.LEFT, padx=20, pady=20)

subtitle_label = tk.Label(
    header_frame, text="Your Personal Finance Learning Assistant", font=("Segoe UI", 11), bg="#1976d2", fg="#bbdefb"
)
subtitle_label.pack(side=tk.LEFT, padx=(0, 20), pady=20)

status_label = tk.Label(
    header_frame, text="✅ Ready to help!", font=("Segoe UI", 10), bg="#1976d2", fg="#4caf50"
)
status_label.pack(side=tk.RIGHT, padx=20, pady=20)

# --- Main Content Frame (inside main_app_frame) ---
content_frame = tk.Frame(main_app_frame, bg="#f5f5f5") # Renamed from main_frame to avoid confusion
content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

# --- Chat Log (inside content_frame) ---
chat_frame = tk.Frame(content_frame, bg="#ffffff", relief="flat", bd=1)
chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

chat_log = scrolledtext.ScrolledText(
    chat_frame,
    wrap=tk.WORD,
    bg="#ffffff",
    fg="#333333",
    font=("Segoe UI", 11),
    relief="flat",
    bd=0,
    padx=15,
    pady=15
)
chat_log.pack(fill=tk.BOTH, expand=True)

# Configure tags for styling
chat_log.tag_config("welcome_anim", foreground="#1976d2", font=("Segoe UI", 16, "bold"), justify="center")
chat_log.tag_config("welcome", foreground="#333333", font=("Segoe UI", 11), justify="left")
chat_log.tag_config("user", foreground="#1976d2", font=("Segoe UI", 11, "bold"))
chat_log.tag_config("nunno_header", foreground="#00796b", font=("Segoe UI", 12, "bold"))
chat_log.tag_config("nunno", foreground="#333333", font=("Segoe UI", 11))
chat_log.tag_config("prediction_result", foreground="#7b1fa2", font=("Segoe UI", 11, "bold"))
chat_log.tag_config("analysis_header", foreground="#f57c00", font=("Segoe UI", 12, "bold"))
chat_log.tag_config("token_key", foreground="#1976d2", font=("Segoe UI", 10, "bold"))
chat_log.tag_config("token_value", foreground="#333333", font=("Segoe UI", 10))
chat_log.tag_config("simulation_header", foreground="#d32f2f", font=("Segoe UI", 12, "bold"))
chat_log.tag_config("simulation_result", foreground="#333333", font=("Segoe UI", 10))
chat_log.tag_config("separator", foreground="#cccccc", font=("Segoe UI", 8))
chat_log.tag_config("error", foreground="#d32f2f", font=("Segoe UI", 10))

# --- Examples Container (inside content_frame) ---
examples_container = tk.Frame(content_frame, bg="#f8f9fa", relief="flat", bd=1)
examples_container.pack(fill=tk.X, pady=(0, 10))


# --- Input Frame (inside content_frame) ---
input_frame = tk.Frame(content_frame, bg="#ffffff", relief="flat", bd=1)
input_frame.pack(fill=tk.X)

# Input container
input_container = tk.Frame(input_frame, bg="#ffffff")
input_container.pack(fill=tk.X, padx=15, pady=15)

# Entry field
entry = tk.Entry(
    input_container,
    font=("Segoe UI", 12),
    bg="#f8f9fa",
    fg="#333333",
    relief="flat",
    bd=0,
    insertbackground="#1976d2"
)
entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=(0, 10))

def on_enter(event=None):
    prompt = entry.get().strip()
    # Check if a prompt exists AND either no thread is active OR the previous thread was stopped
    if prompt and (current_thread is None or not current_thread.is_alive() or stop_flag):
        chat_log.insert(tk.END, f"\n👤 You: {prompt}\n", "user")
        chat_log.see(tk.END)
        entry.delete(0, tk.END)
        
        # Clear examples after the first question
        for widget in examples_container.winfo_children():
            widget.destroy()
        examples_container.pack_forget()
        
        handle_question(prompt)
    elif prompt and current_thread and current_thread.is_alive():
        messagebox.showinfo("Nunno AI", "Nunno is already processing a request. Please wait or click 'Stop Response' to interrupt.")


entry.bind("<Return>", on_enter)

# Ask button
ask_btn = tk.Button(
    input_container,
    text="Ask Nunno", # Use short name
    command=on_enter,
    bg="#1976d2",
    fg="white",
    font=("Segoe UI", 11, "bold"),
    relief="flat",
    bd=0,
    padx=20,
    pady=10,
    cursor="hand2"
)

chart_btn = tk.Button(
    input_container,
    text="📷 Chart Analysis",
    command=lambda: threading.Thread(target=chart_analysis_thread).start(),
    bg="#8E24AA",
    fg="white",
    font=("Segoe UI", 11, "bold"),
    relief="flat",
    bd=0,
    padx=20,
    pady=10,
    cursor="hand2"
)
chart_btn.pack(side=tk.LEFT, padx=(0,10))


ask_btn.pack(side=tk.LEFT, padx=(0, 10))

# Stop button
stop_btn = tk.Button(
    input_container,
    text="Stop Response",
    command=stop_response,
    bg="#d32f2f",
    fg="white",
    font=("Segoe UI", 11, "bold"),
    relief="flat",
    bd=0,
    padx=20,
    pady=10,
    cursor="hand2",
    state="disabled" # Initially disabled
)
stop_btn.pack(side=tk.LEFT, padx=(0,10)) # Added padx for spacing

# New Chat button
new_chat_btn = tk.Button(
    input_container,
    text="New Chat",
    command=new_chat,
    bg="#607d8b", # A neutral color for new chat
    fg="white",
    font=("Segoe UI", 11, "bold"),
    relief="flat",
    bd=0,
    padx=20,
    pady=10,
    cursor="hand2"
)
new_chat_btn.pack(side=tk.LEFT)


# === Welcome Screen UI ===
welcome_frame = tk.Frame(root, bg="#f5f5f5")

welcome_title = tk.Label(
    welcome_frame,
    text="Welcome to Numinous Nexus AI!", # Updated welcome title
    font=("Segoe UI", 24, "bold"),
    bg="#f5f5f5",
    fg="#1976d2"
)
welcome_title.pack(pady=40)

# Name Input
name_label = tk.Label(
    welcome_frame,
    text="Your Name:",
    font=("Segoe UI", 12),
    bg="#f5f5f5",
    fg="#333333"
)
name_label.pack(pady=5)
name_entry = tk.Entry(
    welcome_frame,
    font=("Segoe UI", 12),
    width=30,
    relief="flat",
    bd=1,
    bg="#ffffff",
    fg="#333333"
)
name_entry.pack(ipady=5)

# Age Input
age_label = tk.Label(
    welcome_frame,
    text="Your Age (optional):",
    font=("Segoe UI", 12),
    bg="#f5f5f5",
    fg="#333333"
)
age_label.pack(pady=10)
age_entry = tk.Entry(
    welcome_frame,
    font=("Segoe UI", 12),
    width=30,
    relief="flat",
    bd=1,
    bg="#ffffff",
    fg="#333333"
)
age_entry.pack(ipady=5)

# Start Chat Button
def start_chat_session():
    global user_name, user_age, conversation_history, welcome_shown

    name_input = name_entry.get().strip()
    age_input = age_entry.get().strip()

    if not name_input:
        messagebox.showerror("Input Error", "Please enter your name to proceed.")
        return

    user_name = name_input
    if age_input:
        try:
            user_age = int(age_input)
            if user_age <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid age (a positive number) or leave it blank.")
            return
    else:
        user_age = "N/A" # Keep default if no age entered

    # Hide welcome frame and show main app frame
    welcome_frame.pack_forget()
    main_app_frame.pack(fill=tk.BOTH, expand=True)

    # Initialize conversation history with the personalized system prompt
    formatted_system_prompt = SYSTEM_PROMPT_FORMAT.format(user_name=user_name, user_age=user_age)
    conversation_history.append({"role": "system", "content": formatted_system_prompt})
    
    # Start the chat experience with personalized welcome
    welcome_shown = False # Ensure animation plays for the main app
    show_welcome_animation()


start_btn = tk.Button(
    welcome_frame,
    text="Start Chat with Nunno", # Use short name
    command=start_chat_session,
    bg="#1976d2",
    fg="white",
    font=("Segoe UI", 14, "bold"),
    relief="flat",
    bd=0,
    padx=30,
    pady=15,
    cursor="hand2"
)
start_btn.pack(pady=40)

# --- Initial Call to show the Welcome Screen ---
welcome_frame.pack(fill=tk.BOTH, expand=True) # Show the welcome frame initially

root.mainloop()