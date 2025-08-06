import streamlit as st
import requests
import numpy as np
from fuzzywuzzy import process

st.set_page_config(
    page_title="Tokenomics Analysis - Nunno AI",
    page_icon="💰",
    layout="wide"
)

# Custom CSS for dark theme consistency
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #0e1117 0%, #1a1d24 100%);
    }
    
    [data-testid="metric-container"] {
        background-color: rgba(30, 35, 41, 0.8);
        border: 1px solid rgba(0, 212, 170, 0.2);
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button {
        background: linear-gradient(45deg, #00d4aa, #0088cc);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(45deg, #00b894, #0074cc);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 212, 170, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# Check if profile is set up
if not st.session_state.get("profile_setup", False):
    st.error("Please set up your profile first!")
    if st.button("Go to Home"):
        st.switch_page("app.py")
    st.stop()

st.title("💰 Tokenomics Analysis")
st.markdown(f"Analyze cryptocurrency investments and tokenomics for {st.session_state.user_name}")

# Tokenomics functions
@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_historical_prices(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=365"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        return [p[1] for p in data["prices"]]
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching historical prices for {coin_id}: {e}")
        return None

def calculate_cagr_and_volatility(prices):
    try:
        returns = [np.log(prices[i+1] / prices[i]) for i in range(len(prices)-1)]
        if not returns:
            return None, None, None
        avg_daily_return = np.mean(returns)
        daily_volatility = np.std(returns)
        trading_days = 365
        annual_return = np.exp(avg_daily_return * trading_days) - 1
        annual_volatility = daily_volatility * np.sqrt(trading_days)
        conservative_return = annual_return * 0.5
        return annual_return, annual_volatility, conservative_return
    except Exception as e:
        st.error(f"Error calculating CAGR and Volatility: {e}")
        return None, None, None

@st.cache_data(ttl=300)
def suggest_similar_tokens(user_input):
    try:
        res = requests.get("https://api.coingecko.com/api/v3/coins/list")
        res.raise_for_status()
        coin_list = res.json()
        coin_ids = [coin['id'] for coin in coin_list]
        best_matches = process.extract(user_input.lower(), coin_ids, limit=5)
        return [match[0] for match in best_matches if match[1] > 60]
    except requests.exceptions.RequestException as e:
        st.error(f"Error suggesting similar tokens: {e}")
        return []

@st.cache_data(ttl=300)
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
        fdv_mcap_ratio = (fdv / mcap) if mcap and mcap != 0 else None

        healthy = "✅ This coin seems healthy!" if circ_percent and circ_percent > 50 and fdv_mcap_ratio and fdv_mcap_ratio < 2 else "⚠️ Warning: This coin might be risky or inflated."

        prices = fetch_historical_prices(coin_id)
        if not prices or len(prices) < 2:
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
            "Should I Invest?": healthy,
            "raw_data": {
                "price": price,
                "mcap": mcap,
                "fdv": fdv,
                "circulating": circulating,
                "total": total,
                "circ_percent": circ_percent,
                "fdv_mcap_ratio": fdv_mcap_ratio,
                "cagr": cagr,
                "volatility": volatility,
                "conservative_cagr": conservative_cagr
            }
        }
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching token data for {coin_id}: {e}")
        return None

# Sidebar controls
with st.sidebar:
    st.markdown("### 💰 Tokenomics Settings")
    
    # Coin input
    coin_input = st.text_input(
        "Cryptocurrency",
        value="bitcoin",
        help="Enter the coin ID (e.g., bitcoin, ethereum, cardano)"
    )
    
    # Investment amount
    investment_amount = st.number_input(
        "Investment Amount ($)",
        min_value=1.0,
        value=1000.0,
        step=100.0,
        help="How much are you planning to invest?"
    )
    
    st.markdown("---")
    
    # Analyze button
    if st.button("🔍 Analyze Token", type="primary"):
        st.session_state.run_tokenomics = True
        st.session_state.current_coin = coin_input.lower().strip()
        st.session_state.investment_amt = investment_amount
    
    st.markdown("---")
    
    st.markdown("""
    ### 💡 Tokenomics Explained
    
    **Key Metrics:**
    - **Market Cap**: Total value of all circulating coins
    - **FDV**: Fully Diluted Valuation (if all coins were unlocked)
    - **Circulating Supply**: Coins currently available
    - **Total Supply**: Maximum possible coins
    
    **Health Indicators:**
    - **Circulating %**: Higher is generally better (>50%)
    - **FDV/Market Cap**: Lower is better (<2)
    - **CAGR**: Historical annual growth rate
    - **Volatility**: Price fluctuation level
    
    **Popular Coins:**
    - bitcoin
    - ethereum  
    - cardano
    - solana
    - chainlink
    - polygon
    """)

# Main analysis section
if st.session_state.get("run_tokenomics", False):
    coin_id = st.session_state.current_coin
    investment = st.session_state.investment_amt
    
    with st.spinner(f"Analyzing {coin_id.upper()}..."):
        try:
            # Fetch token data
            token_data = fetch_token_data(coin_id, investment)
            
            if token_data is None:
                st.error(f"❌ Could not find data for '{coin_id}'. Please check the spelling.")
                
                # Suggest similar tokens
                suggestions = suggest_similar_tokens(coin_id)
                if suggestions:
                    st.markdown("### 💡 Did you mean one of these?")
                    cols = st.columns(min(3, len(suggestions)))
                    for i, suggestion in enumerate(suggestions[:3]):
                        with cols[i]:
                            if st.button(f"🔍 {suggestion}", key=f"suggest_{i}"):
                                st.session_state.current_coin = suggestion
                                st.rerun()
            else:
                # Display results
                st.success(f"✅ Analysis completed for {token_data['Coin Name & Symbol']}")
                
                raw = token_data["raw_data"]
                
                # Overview metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Current Price",
                        f"${raw['price']:,.6f}"
                    )
                
                with col2:
                    st.metric(
                        "Market Cap",
                        f"${raw['mcap'] / 1e9:,.2f}B"
                    )
                
                with col3:
                    fdv_color = "🟢" if raw['fdv_mcap_ratio'] and raw['fdv_mcap_ratio'] < 2 else "🟡" if raw['fdv_mcap_ratio'] and raw['fdv_mcap_ratio'] < 5 else "🔴"
                    st.metric(
                        "FDV/MCap Ratio",
                        f"{fdv_color} {raw['fdv_mcap_ratio']:.2f}" if raw['fdv_mcap_ratio'] else "N/A"
                    )
                
                with col4:
                    circ_color = "🟢" if raw['circ_percent'] and raw['circ_percent'] > 70 else "🟡" if raw['circ_percent'] and raw['circ_percent'] > 50 else "🔴"
                    st.metric(
                        "Circulating %",
                        f"{circ_color} {raw['circ_percent']:.1f}%" if raw['circ_percent'] else "N/A"
                    )
                
                # Investment projections
                if raw['conservative_cagr'] is not None:
                    st.markdown("### 💵 Investment Projections")
                    
                    proj_col1, proj_col2, proj_col3 = st.columns(3)
                    
                    monthly_return = investment * raw['conservative_cagr'] / 12
                    yearly_return = investment * raw['conservative_cagr']
                    
                    with proj_col1:
                        st.metric(
                            "Investment Amount",
                            f"${investment:,.2f}"
                        )
                    
                    with proj_col2:
                        st.metric(
                            "Expected Monthly Return",
                            f"${monthly_return:,.2f}",
                            f"{raw['conservative_cagr'] * 100 / 12:.2f}%"
                        )
                    
                    with proj_col3:
                        st.metric(
                            "Expected Yearly Return", 
                            f"${yearly_return:,.2f}",
                            f"{raw['conservative_cagr'] * 100:.2f}%"
                        )
                    
                    # Risk assessment
                    st.markdown("### ⚖️ Risk Assessment")
                    
                    risk_factors = []
                    
                    if raw['fdv_mcap_ratio'] and raw['fdv_mcap_ratio'] > 5:
                        risk_factors.append("🔴 **High FDV/MCap Ratio**: Large potential dilution from unlocked tokens")
                    
                    if raw['circ_percent'] and raw['circ_percent'] < 50:
                        risk_factors.append("🟡 **Low Circulating Supply**: Many tokens still locked/unvested")
                    
                    if raw['volatility'] and raw['volatility'] > 1:
                        risk_factors.append("🟡 **High Volatility**: Expect significant price swings")
                    
                    if not risk_factors:
                        st.success("✅ **Low Risk Profile**: This token shows healthy tokenomics!")
                    else:
                        for factor in risk_factors:
                            st.warning(factor)
                
                # Detailed tokenomics
                st.markdown("### 📊 Detailed Tokenomics")
                
                # Create tabs for different sections
                tab1, tab2, tab3 = st.tabs(["📈 Supply Metrics", "💰 Market Data", "📊 Performance"])
                
                with tab1:
                    st.markdown("#### Supply Information")
                    supply_col1, supply_col2 = st.columns(2)
                    
                    with supply_col1:
                        st.markdown(f"**Total Supply:** {token_data['Total Supply (M)']}")
                        st.markdown(f"**Circulating Supply:** {token_data['Circulating Supply (M)']}")
                        st.markdown(f"**Circulating %:** {token_data['Circulating Supply %']}")
                    
                    with supply_col2:
                        st.markdown(f"**FDV:** {token_data['FDV (B)']}")
                        st.markdown(f"**FDV/MCap Ratio:** {token_data['FDV/Market Cap Ratio']}")
                        
                        # Visual representation
                        if raw['circ_percent']:
                            st.progress(raw['circ_percent'] / 100, f"Circulating: {raw['circ_percent']:.1f}%")
                
                with tab2:
                    st.markdown("#### Market Information")
                    market_col1, market_col2 = st.columns(2)
                    
                    with market_col1:
                        st.markdown(f"**Current Price:** {token_data['Current Price ($)']}")
                        st.markdown(f"**Market Cap:** {token_data['Market Cap (B)']}")
                    
                    with market_col2:
                        # Health indicator
                        if "healthy" in token_data["Should I Invest?"]:
                            st.success(token_data["Should I Invest?"])
                        else:
                            st.warning(token_data["Should I Invest?"])
                
                with tab3:
                    st.markdown("#### Historical Performance")
                    
                    if raw['cagr'] is not None:
                        perf_col1, perf_col2 = st.columns(2)
                        
                        with perf_col1:
                            st.markdown(f"**Historical CAGR:** {token_data['Historical Annual Return (CAGR)']}")
                            st.markdown(f"**Conservative CAGR:** {token_data['Realistic Yearly Return (50% CAGR)']}")
                        
                        with perf_col2:
                            st.markdown(f"**Volatility:** {token_data['Annual Volatility']}")
                            
                            # Risk-return visualization
                            if raw['volatility'] and raw['conservative_cagr']:
                                risk_return_ratio = raw['conservative_cagr'] / raw['volatility']
                                st.metric("Risk-Return Ratio", f"{risk_return_ratio:.2f}")
                                
                                if risk_return_ratio > 0.5:
                                    st.success("🟢 Good risk-adjusted returns")
                                elif risk_return_ratio > 0.2:
                                    st.warning("🟡 Moderate risk-adjusted returns")
                                else:
                                    st.error("🔴 Poor risk-adjusted returns")
                    else:
                        st.info("Historical performance data not available.")
                
                # Investment recommendation
                st.markdown("### 💡 Investment Recommendation")
                
                recommendation_score = 0
                factors = []
                
                # Scoring based on various factors
                if raw['fdv_mcap_ratio'] and raw['fdv_mcap_ratio'] < 2:
                    recommendation_score += 2
                    factors.append("✅ Low dilution risk")
                elif raw['fdv_mcap_ratio'] and raw['fdv_mcap_ratio'] < 5:
                    recommendation_score += 1
                    factors.append("⚠️ Moderate dilution risk")
                else:
                    factors.append("❌ High dilution risk")
                
                if raw['circ_percent'] and raw['circ_percent'] > 70:
                    recommendation_score += 2
                    factors.append("✅ High token circulation")
                elif raw['circ_percent'] and raw['circ_percent'] > 50:
                    recommendation_score += 1
                    factors.append("⚠️ Moderate token circulation")
                else:
                    factors.append("❌ Low token circulation")
                
                if raw['conservative_cagr'] and raw['conservative_cagr'] > 0.5:
                    recommendation_score += 2
                    factors.append("✅ Strong historical performance")
                elif raw['conservative_cagr'] and raw['conservative_cagr'] > 0.2:
                    recommendation_score += 1
                    factors.append("⚠️ Moderate historical performance")
                elif raw['conservative_cagr'] and raw['conservative_cagr'] > 0:
                    factors.append("⚠️ Weak historical performance")
                else:
                    factors.append("❌ Negative historical performance")
                
                # Final recommendation
                if recommendation_score >= 5:
                    st.success("""
                    **🟢 STRONG BUY RECOMMENDATION**
                    
                    This token shows excellent tokenomics with low risk factors and strong potential returns.
                    """)
                elif recommendation_score >= 3:
                    st.warning("""
                    **🟡 MODERATE BUY RECOMMENDATION**
                    
                    This token has decent tokenomics but consider the risk factors carefully.
                    """)
                else:
                    st.error("""
                    **🔴 CAUTIOUS APPROACH RECOMMENDED**
                    
                    This token has concerning tokenomics. Proceed with caution and consider smaller position sizes.
                    """)
                
                # List all factors
                st.markdown("**Analysis Factors:**")
                for factor in factors:
                    st.markdown(f"- {factor}")
                
        except Exception as e:
            st.error(f"An error occurred during analysis: {str(e)}")

else:
    # Default view
    st.info("👆 Enter a cryptocurrency name in the sidebar and click 'Analyze Token' to get started!")
    
    st.markdown("""
    ### 🎯 How to Use Tokenomics Analysis
    
    1. **Enter Coin ID**: Use the coin's CoinGecko ID (e.g., 'bitcoin', 'ethereum', 'cardano')
    2. **Set Investment Amount**: How much you're planning to invest
    3. **Click Analyze**: Get comprehensive tokenomics analysis
    
    ### 💰 What You'll Get
    
    - **Supply Metrics**: Total supply, circulating supply, and percentages
    - **Market Data**: Price, market cap, and FDV information
    - **Investment Projections**: Expected monthly and yearly returns
    - **Risk Assessment**: Identification of potential risk factors
    - **Investment Recommendation**: Overall buy/hold/avoid recommendation
    
    ### 🔍 Key Things to Look For
    
    **Healthy Tokenomics:**
    - ✅ Circulating supply > 70% of total supply
    - ✅ FDV/Market Cap ratio < 2
    - ✅ Positive historical performance
    - ✅ Reasonable volatility levels
    
    **Red Flags:**
    - ❌ Very low circulating supply (<50%)
    - ❌ High FDV/Market Cap ratio (>5)
    - ❌ Extreme volatility (>200% annually)
    - ❌ Consistently negative returns
    
    ### 📚 Popular Cryptocurrencies to Analyze
    
    **Large Cap:**
    - bitcoin
    - ethereum
    - binancecoin
    
    **Mid Cap:**
    - cardano
    - solana  
    - chainlink
    - polygon
    
    **DeFi Tokens:**
    - uniswap
    - aave
    - compound
    - maker
    """)
