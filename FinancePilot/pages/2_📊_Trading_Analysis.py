import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from betterpredictormodule import TradingAnalyzer
from datetime import datetime

st.set_page_config(
    page_title="Trading Analysis - Nunno AI",
    page_icon="📊",
    layout="wide"
)



# Check if profile is set up
if not st.session_state.get("profile_setup", False):
    st.error("Please set up your profile first!")
    if st.button("Go to Home"):
        st.switch_page("app.py")
    st.stop()

st.title("📊 Trading Analysis")
st.markdown(f"Advanced technical analysis with confluence signals for {st.session_state.user_name}")

# Initialize the analyzer
@st.cache_resource
def get_analyzer():
    return TradingAnalyzer()

analyzer = get_analyzer()

# Sidebar controls
with st.sidebar:
    st.markdown("### 📊 Analysis Settings")
    
    # Symbol input
    symbol = st.text_input("Trading Symbol", value="BTCUSDT", help="Enter a trading symbol (e.g., BTCUSDT, ETHUSDT). Auto-fallback to CoinGecko if Binance is restricted.")
    
    # Interval selection
    interval = st.selectbox(
        "Timeframe",
        ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
        index=2,  # Default to 15m
        help="Select the timeframe for analysis"
    )
    
    # Data points
    limit = st.slider("Data Points", min_value=100, max_value=1000, value=500, step=100)
    
    st.markdown("---")
    
    # Analysis button
    if st.button("🔍 Analyze", type="primary"):
        st.session_state.run_analysis = True
    
    st.markdown("---")
    
    st.markdown("""
    ### 📈 What is Confluence Analysis?
    
    Confluence analysis combines multiple technical indicators to identify high-probability trading setups.
    
    **Signal Types:**
    - 🟢 **Bullish**: Multiple indicators suggest upward movement
    - 🔴 **Bearish**: Multiple indicators suggest downward movement  
    - 🟡 **Neutral**: Mixed or weak signals
    
    **Strength Levels:**
    - **Strong**: 5+ confluences
    - **Medium**: 3-4 confluences
    - **Weak**: <3 confluences
    
    **Data Sources:**
    - Primary: Binance API (real-time)
    - Fallback: CoinGecko API (global access)
    """)

# Main analysis section
if st.session_state.get("run_analysis", False):
    
    with st.spinner(f"Analyzing {symbol.upper()} on {interval} timeframe..."):
        try:
            # Get comprehensive analysis
            analysis = analyzer.get_comprehensive_analysis(symbol, interval)
            
            if "error" in analysis:
                st.error(f"Analysis failed: {analysis['error']}")
            else:
                # Display results
                st.success(f"✅ Analysis completed for {analysis['symbol']}")
                
                # Overview metrics
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric(
                        "Current Price",
                        f"${analysis['current_price']:.6f}"
                    )
                
                with col2:
                    signal_color = "🟢" if analysis['overall_signal'] == "BULLISH" else "🔴" if analysis['overall_signal'] == "BEARISH" else "🟡"
                    st.metric(
                        "Overall Signal",
                        f"{signal_color} {analysis['overall_signal']}"
                    )
                
                with col3:
                    st.metric(
                        "Signal Strength",
                        analysis['signal_strength']
                    )
                
                with col4:
                    st.metric(
                        "Bullish Confluences",
                        analysis['confluence_counts']['bullish']
                    )
                
                with col5:
                    st.metric(
                        "Bearish Confluences", 
                        analysis['confluence_counts']['bearish']
                    )
                
                # Key levels
                st.markdown("### 🎯 Key Levels")
                levels_col1, levels_col2, levels_col3 = st.columns(3)
                
                with levels_col1:
                    st.metric("🔴 Resistance", f"${analysis['key_levels']['resistance']:.6f}")
                
                with levels_col2:
                    st.metric("🟡 Pivot", f"${analysis['key_levels']['pivot']:.6f}")
                
                with levels_col3:
                    st.metric("🟢 Support", f"${analysis['key_levels']['support']:.6f}")
                
                # Technical snapshot
                st.markdown("### 📋 Technical Snapshot")
                tech_col1, tech_col2, tech_col3, tech_col4, tech_col5 = st.columns(5)
                
                tech = analysis['technical_snapshot']
                
                with tech_col1:
                    rsi_color = "🟢" if tech['RSI_14'] < 30 else "🔴" if tech['RSI_14'] > 70 else "🟡"
                    st.metric("RSI (14)", f"{rsi_color} {tech['RSI_14']:.1f}")
                
                with tech_col2:
                    macd_color = "🟢" if tech['MACD'] > 0 else "🔴"
                    st.metric("MACD", f"{macd_color} {tech['MACD']:.6f}")
                
                with tech_col3:
                    adx_color = "🟢" if tech['ADX'] > 25 else "🟡"
                    st.metric("ADX", f"{adx_color} {tech['ADX']:.1f}")
                
                with tech_col4:
                    atr_color = "🔴" if tech['ATR_Percent'] > 5 else "🟡" if tech['ATR_Percent'] > 2 else "🟢"
                    st.metric("ATR%", f"{atr_color} {tech['ATR_Percent']:.2f}%")
                
                with tech_col5:
                    bb_color = "🟢" if tech['BB_Position'] < 0.2 else "🔴" if tech['BB_Position'] > 0.8 else "🟡"
                    st.metric("BB Position", f"{bb_color} {tech['BB_Position']:.3f}")
                
                # Detailed confluences
                st.markdown("### 🔍 Detailed Confluence Analysis")
                
                confluences = analysis['confluences']
                
                # Create tabs for different confluence types
                tab1, tab2, tab3 = st.tabs(["🟢 Bullish Confluences", "🔴 Bearish Confluences", "🟡 Neutral Confluences"])
                
                with tab1:
                    if confluences['bullish']:
                        for i, conf in enumerate(confluences['bullish'], 1):
                            with st.expander(f"{i}. {conf['indicator']} ({conf['strength']})"):
                                st.markdown(f"**Timeframe:** {conf['timeframe']}")
                                st.markdown(f"**Condition:** {conf['condition']}")
                                st.markdown(f"**Implication:** {conf['implication']}")
                    else:
                        st.info("No bullish confluences detected.")
                
                with tab2:
                    if confluences['bearish']:
                        for i, conf in enumerate(confluences['bearish'], 1):
                            with st.expander(f"{i}. {conf['indicator']} ({conf['strength']})"):
                                st.markdown(f"**Timeframe:** {conf['timeframe']}")
                                st.markdown(f"**Condition:** {conf['condition']}")
                                st.markdown(f"**Implication:** {conf['implication']}")
                    else:
                        st.info("No bearish confluences detected.")
                
                with tab3:
                    if confluences['neutral']:
                        for i, conf in enumerate(confluences['neutral'], 1):
                            with st.expander(f"{i}. {conf['indicator']} ({conf['strength']})"):
                                st.markdown(f"**Timeframe:** {conf['timeframe']}")
                                st.markdown(f"**Condition:** {conf['condition']}")
                                st.markdown(f"**Implication:** {conf['implication']}")
                    else:
                        st.info("No neutral confluences detected.")
                
                # Trading recommendations
                st.markdown("### 💡 Trading Recommendations")
                
                if analysis['overall_signal'] == "BULLISH":
                    st.success("""
                    **🟢 BULLISH BIAS DETECTED**
                    
                    **Potential Actions:**
                    - Consider long positions on pullbacks to support levels
                    - Watch for continuation above resistance
                    - Use dynamic EMAs as trailing stop levels
                    - Monitor volume for confirmation
                    
                    **Risk Management:**
                    - Place stops below key support levels
                    - Consider position sizing based on ATR
                    - Take partial profits at resistance levels
                    """)
                
                elif analysis['overall_signal'] == "BEARISH":
                    st.error("""
                    **🔴 BEARISH BIAS DETECTED**
                    
                    **Potential Actions:**
                    - Consider short positions on rallies to resistance levels
                    - Watch for continuation below support
                    - Use dynamic EMAs as trailing stop levels
                    - Monitor volume for confirmation
                    
                    **Risk Management:**
                    - Place stops above key resistance levels
                    - Consider position sizing based on ATR
                    - Take partial profits at support levels
                    """)
                
                else:
                    st.warning("""
                    **🟡 NEUTRAL/MIXED SIGNALS**
                    
                    **Potential Actions:**
                    - Wait for clearer directional signals
                    - Consider range trading between support/resistance
                    - Watch for breakout setups
                    - Avoid large position sizes
                    
                    **Risk Management:**
                    - Use tight stops in ranging markets
                    - Reduce position sizes
                    - Wait for confluence to increase
                    """)
                
                # Price Chart
                st.markdown("### 📈 Price Chart & Technical Indicators")
                
                try:
                    # Get the full dataset for charting
                    chart_df = analyzer.fetch_binance_ohlcv(symbol, interval)
                    chart_df = analyzer.add_comprehensive_indicators(chart_df)
                    
                    if not chart_df.empty:
                        # Create subplots
                        fig = make_subplots(
                            rows=4, cols=1,
                            shared_xaxes=True,
                            vertical_spacing=0.05,
                            subplot_titles=('Price & Moving Averages', 'RSI', 'MACD', 'Volume'),
                            row_weights=[0.5, 0.2, 0.2, 0.1]
                        )
                        
                        # Candlestick chart
                        fig.add_trace(
                            go.Candlestick(
                                x=chart_df.index,
                                open=chart_df['Open'],
                                high=chart_df['High'],
                                low=chart_df['Low'],
                                close=chart_df['Close'],
                                name="Price",
                                increasing_line_color='#00d4aa',
                                decreasing_line_color='#ff6b6b'
                            ),
                            row=1, col=1
                        )
                        
                        # EMAs
                        fig.add_trace(
                            go.Scatter(
                                x=chart_df.index,
                                y=chart_df['EMA_21'],
                                name='EMA 21',
                                line=dict(color='#ffa726', width=1.5)
                            ),
                            row=1, col=1
                        )
                        
                        fig.add_trace(
                            go.Scatter(
                                x=chart_df.index,
                                y=chart_df['EMA_50'],
                                name='EMA 50',
                                line=dict(color='#42a5f5', width=1.5)
                            ),
                            row=1, col=1
                        )
                        
                        # Bollinger Bands
                        fig.add_trace(
                            go.Scatter(
                                x=chart_df.index,
                                y=chart_df['BB_Upper'],
                                name='BB Upper',
                                line=dict(color='rgba(128,128,128,0.3)', width=1),
                                showlegend=False
                            ),
                            row=1, col=1
                        )
                        
                        fig.add_trace(
                            go.Scatter(
                                x=chart_df.index,
                                y=chart_df['BB_Lower'],
                                name='BB Lower',
                                line=dict(color='rgba(128,128,128,0.3)', width=1),
                                fill='tonexty',
                                fillcolor='rgba(128,128,128,0.1)',
                                showlegend=False
                            ),
                            row=1, col=1
                        )
                        
                        # RSI
                        fig.add_trace(
                            go.Scatter(
                                x=chart_df.index,
                                y=chart_df['RSI_14'],
                                name='RSI',
                                line=dict(color='#9c27b0', width=2)
                            ),
                            row=2, col=1
                        )
                        
                        # RSI levels
                        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
                        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)
                        fig.add_hline(y=50, line_dash="dot", line_color="gray", opacity=0.3, row=2, col=1)
                        
                        # MACD
                        fig.add_trace(
                            go.Scatter(
                                x=chart_df.index,
                                y=chart_df['MACD'],
                                name='MACD',
                                line=dict(color='#2196f3', width=2)
                            ),
                            row=3, col=1
                        )
                        
                        fig.add_trace(
                            go.Scatter(
                                x=chart_df.index,
                                y=chart_df['MACD_Signal'],
                                name='MACD Signal',
                                line=dict(color='#ff9800', width=2)
                            ),
                            row=3, col=1
                        )
                        
                        # MACD Histogram
                        colors = ['green' if val >= 0 else 'red' for val in chart_df['MACD_Histogram']]
                        fig.add_trace(
                            go.Bar(
                                x=chart_df.index,
                                y=chart_df['MACD_Histogram'],
                                name='MACD Histogram',
                                marker_color=colors,
                                opacity=0.7
                            ),
                            row=3, col=1
                        )
                        
                        # Volume
                        fig.add_trace(
                            go.Bar(
                                x=chart_df.index,
                                y=chart_df['Volume'],
                                name='Volume',
                                marker_color='rgba(158,158,158,0.5)'
                            ),
                            row=4, col=1
                        )
                        
                        # Update layout for light theme
                        fig.update_layout(
                            title=f"{symbol.upper()} Technical Analysis",
                            template="plotly_white",
                            height=800,
                            showlegend=True,
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            )
                        )
                        
                        # Update y-axis ranges
                        fig.update_yaxes(range=[0, 100], row=2, col=1)  # RSI
                        
                        # Remove rangeslider
                        fig.update_layout(xaxis_rangeslider_visible=False)
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Chart data not available")
                        
                except Exception as e:
                    st.error(f"Failed to generate chart: {str(e)}")
                
                # Display formatted analysis
                st.markdown("### 📄 Full Analysis Report")
                
                formatted_analysis = analyzer.format_confluence_analysis(analysis)
                st.markdown(formatted_analysis)
                
        except Exception as e:
            st.error(f"An error occurred during analysis: {str(e)}")

else:
    # Default view
    st.info("👆 Configure your analysis settings in the sidebar and click 'Analyze' to get started!")
    
    st.markdown("""
    ### 🎯 How to Use Trading Analysis
    
    1. **Select Symbol**: Enter any Binance trading pair (e.g., BTCUSDT, ETHUSDT, ADAUSDT)
    2. **Choose Timeframe**: Select from 1m to 1d based on your trading style
    3. **Set Data Points**: More data = more reliable signals (recommended: 500+)
    4. **Click Analyze**: Get comprehensive confluence analysis
    
    ### 📊 What You'll Get
    
    - **Overall Signal**: Bullish, Bearish, or Neutral with strength rating
    - **Key Levels**: Support, resistance, and pivot points
    - **Technical Snapshot**: Quick view of major indicators
    - **Detailed Confluences**: All bullish, bearish, and neutral signals
    - **Trading Recommendations**: Actionable insights based on analysis
    
    ### 🎓 Understanding Confluences
    
    **Momentum Indicators:**
    - RSI: Measures overbought/oversold conditions
    - Stochastic: Another momentum oscillator
    - Williams %R: Similar to Stochastic
    
    **Trend Indicators:**
    - EMA Alignment: Multiple EMAs trending same direction
    - MACD: Moving average convergence divergence
    - ADX: Trend strength measurement
    
    **Volatility Indicators:**
    - Bollinger Bands: Price position relative to bands
    - ATR: Average True Range for volatility
    - Keltner Channels: Another volatility indicator
    
    **Volume Indicators:**
    - Volume Ratio: Current vs average volume
    - Chaikin Money Flow: Money flow in/out of asset
    """)
