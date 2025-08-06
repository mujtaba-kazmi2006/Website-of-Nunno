import streamlit as st
import requests
import os
from datetime import datetime

st.set_page_config(
    page_title="Market News - Nunno AI",
    page_icon="📰",
    layout="wide"
)



# Check if profile is set up
if not st.session_state.get("profile_setup", False):
    st.error("Please set up your profile first!")
    if st.button("Go to Home"):
        st.switch_page("app.py")
    st.stop()

# API Key
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "b3dfc15d73704bfab32ebb96b5c9885b")

st.title("📰 Market News")
st.markdown(f"Stay updated with the latest financial news, {st.session_state.user_name}")

@st.cache_data(ttl=600)  # Cache for 10 minutes
def fetch_market_news():
    """Fetch latest market news"""
    url = "https://newsapi.org/v2/everything"
    today = datetime.now().strftime("%Y-%m-%d")
    params = {
        "q": "finance OR stock market OR bitcoin OR federal reserve OR inflation OR interest rates",
        "from": today,
        "sortBy": "publishedAt",
        "language": "en",
        "apiKey": NEWS_API_KEY,
        "pageSize": 20,
        "domains": "cnbc.com, bloomberg.com, reuters.com, wsj.com, marketwatch.com, yahoo.com"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        return articles
    except Exception as e:
        st.error(f"Error fetching market news: {e}")
        return []

@st.cache_data(ttl=600)
def fetch_crypto_news():
    """Fetch crypto-specific news"""
    url = "https://newsapi.org/v2/everything"
    today = datetime.now().strftime("%Y-%m-%d")
    params = {
        "q": "bitcoin OR ethereum OR cryptocurrency OR crypto OR blockchain OR DeFi",
        "from": today,
        "sortBy": "publishedAt",
        "language": "en",
        "apiKey": NEWS_API_KEY,
        "pageSize": 20,
        "domains": "coindesk.com, cointelegraph.com, decrypt.co, crypto.news"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        return articles
    except Exception as e:
        st.error(f"Error fetching crypto news: {e}")
        return []

def display_articles(articles, title):
    """Display articles in a nice format"""
    if not articles:
        st.info("No recent articles found.")
        return
    
    st.subheader(title)
    
    for i, article in enumerate(articles[:10]):  # Show top 10 articles
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Title and description
                st.markdown(f"**{article['title']}**")
                if article.get('description'):
                    st.markdown(f"*{article['description']}*")
                
                # Source and date
                published_at = datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00'))
                formatted_time = published_at.strftime('%Y-%m-%d %H:%M UTC')
                
                st.markdown(f"📰 **{article['source']['name']}** • 🕒 {formatted_time}")
                
                # Read more link
                if article.get('url'):
                    st.markdown(f"[📖 Read Full Article]({article['url']})")
            
            with col2:
                # Article image if available
                if article.get('urlToImage'):
                    try:
                        st.image(article['urlToImage'], width=200)
                    except:
                        st.markdown("🖼️ *Image unavailable*")
                else:
                    st.markdown("🖼️ *No image*")
            
            st.markdown("---")

# Sidebar controls
with st.sidebar:
    st.markdown("### 📰 News Settings")
    
    # News category selection
    news_category = st.selectbox(
        "News Category",
        ["General Market", "Cryptocurrency", "Both"],
        help="Choose what type of news to display"
    )
    
    # Refresh button
    if st.button("🔄 Refresh News", type="primary"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("""
    ### 📊 News Sources
    
    **General Market:**
    - CNBC
    - Bloomberg
    - Reuters
    - Wall Street Journal
    - MarketWatch
    - Yahoo Finance
    
    **Cryptocurrency:**
    - CoinDesk
    - Cointelegraph
    - Decrypt
    - Crypto News
    
    ### 🔍 Keywords Covered
    
    **Market News:**
    - Stock Market
    - Federal Reserve
    - Interest Rates
    - Inflation
    - Economic Data
    
    **Crypto News:**
    - Bitcoin & Ethereum
    - Altcoins
    - DeFi
    - Blockchain
    - Regulatory Updates
    """)

# Main content
if news_category in ["General Market", "Both"]:
    with st.spinner("Fetching latest market news..."):
        market_articles = fetch_market_news()
        display_articles(market_articles, "📈 Latest Market News")

if news_category in ["Cryptocurrency", "Both"]:
    with st.spinner("Fetching latest crypto news..."):
        crypto_articles = fetch_crypto_news()
        display_articles(crypto_articles, "₿ Latest Crypto News")

if news_category == "Both":
    # Combine and sort by date for mixed view
    st.markdown("---")
    st.subheader("🔄 All Recent News (Mixed)")
    
    all_articles = []
    if 'market_articles' in locals():
        all_articles.extend(market_articles)
    if 'crypto_articles' in locals():
        all_articles.extend(crypto_articles)
    
    # Sort by publication date
    all_articles.sort(key=lambda x: x['publishedAt'], reverse=True)
    
    # Remove duplicates based on title
    seen_titles = set()
    unique_articles = []
    for article in all_articles:
        if article['title'] not in seen_titles:
            unique_articles.append(article)
            seen_titles.add(article['title'])
    
    if unique_articles:
        for i, article in enumerate(unique_articles[:15]):
            with st.expander(f"📰 {article['title'][:100]}{'...' if len(article['title']) > 100 else ''}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    if article.get('description'):
                        st.markdown(f"**Description:** {article['description']}")
                    
                    # Source and date
                    published_at = datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00'))
                    formatted_time = published_at.strftime('%Y-%m-%d %H:%M UTC')
                    
                    st.markdown(f"📰 **Source:** {article['source']['name']}")
                    st.markdown(f"🕒 **Published:** {formatted_time}")
                    
                    # Category tag
                    is_crypto = any(keyword in article['title'].lower() or 
                                  (article.get('description', '').lower() if article.get('description') else False)
                                  for keyword in ['bitcoin', 'ethereum', 'crypto', 'blockchain', 'defi'])
                    
                    category_tag = "₿ Cryptocurrency" if is_crypto else "📈 Market"
                    st.markdown(f"🏷️ **Category:** {category_tag}")
                    
                    # Read more link
                    if article.get('url'):
                        st.markdown(f"[📖 Read Full Article]({article['url']})")
                
                with col2:
                    if article.get('urlToImage'):
                        try:
                            st.image(article['urlToImage'], width=200)
                        except:
                            st.markdown("🖼️ *Image unavailable*")

# Quick news summary
st.markdown("---")
st.subheader("📊 News Summary")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Market Articles Today", len(market_articles) if 'market_articles' in locals() else 0)

with col2:
    st.metric("Crypto Articles Today", len(crypto_articles) if 'crypto_articles' in locals() else 0)

with col3:
    total_articles = (len(market_articles) if 'market_articles' in locals() else 0) + \
                    (len(crypto_articles) if 'crypto_articles' in locals() else 0)
    st.metric("Total Articles", total_articles)

# Tips section
st.markdown("---")
st.markdown("""
### 💡 How to Use Market News

**📈 For Trading:**
- Look for news that might affect market sentiment
- Pay attention to Federal Reserve announcements
- Watch for economic data releases
- Monitor geopolitical events

**₿ For Crypto:**
- Follow regulatory developments
- Track institutional adoption news
- Monitor DeFi protocol updates
- Watch for major partnerships

**🎯 News Trading Tips:**
- News often creates short-term volatility
- Always verify news from multiple sources
- Be cautious of "buy the rumor, sell the news" scenarios
- Consider the timing of news releases

**⚠️ Important Reminders:**
- News can create false signals
- Market reaction isn't always predictable  
- Combine news with technical analysis
- Don't make decisions based on headlines alone
""")
