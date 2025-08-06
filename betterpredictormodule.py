import requests
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator, StochasticOscillator, WilliamsRIndicator
from ta.trend import EMAIndicator, SMAIndicator, MACD, ADXIndicator, IchimokuIndicator
from ta.volatility import BollingerBands, AverageTrueRange, KeltnerChannel
from ta.volume import OnBalanceVolumeIndicator, ChaikinMoneyFlowIndicator
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class TradingAnalyzer:
    def __init__(self):
        self.confluence_threshold = 3  # Minimum confluences for strong signals
    
    def fetch_coingecko_ohlcv(self, symbol="bitcoin", days=30):
        """Fetch OHLCV data from CoinGecko (global alternative)"""
        # Convert common trading symbols to CoinGecko IDs
        symbol_map = {
            "BTCUSDT": "bitcoin",
            "ETHUSDT": "ethereum", 
            "ADAUSDT": "cardano",
            "SOLUSDT": "solana",
            "DOTUSDT": "polkadot",
            "LINKUSDT": "chainlink",
            "MATICUSDT": "polygon",
            "AVAXUSDT": "avalanche-2",
            "ATOMUSDT": "cosmos",
            "LTCUSDT": "litecoin"
        }
        
        coin_id = symbol_map.get(symbol.upper(), symbol.lower().replace("usdt", ""))
        
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc?vs_currency=usd&days={days}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                raise Exception(f"CoinGecko API Error {response.status_code}: {response.text}")
            
            data = response.json()
            
            # CoinGecko returns [timestamp, open, high, low, close]
            df = pd.DataFrame(data, columns=["timestamp", "Open", "High", "Low", "Close"])
            
            # Convert timestamp and set index
            df['Open Time'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df[["Open Time", "Open", "High", "Low", "Close"]].astype({
                "Open": float, "High": float, "Low": float, "Close": float
            })
            
            # Add synthetic volume (CoinGecko OHLC doesn't include volume)
            # Use price volatility as volume proxy
            df['Volume'] = (df['High'] - df['Low']) * df['Close'] * 1000
            
            df.set_index('Open Time', inplace=True)
            return df
            
        except Exception as e:
            raise Exception(f"Failed to fetch data from CoinGecko: {str(e)}")

    def fetch_binance_ohlcv(self, symbol="BTCUSDT", interval="15m", limit=1000):
        """Fetch OHLCV data from Binance with CoinGecko fallback"""
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol.upper()}&interval={interval}&limit={limit}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                # If Binance fails, try CoinGecko fallback
                if response.status_code == 451:  # Restricted location
                    print(f"Binance restricted in your location, falling back to CoinGecko for {symbol}")
                    return self.fetch_coingecko_ohlcv(symbol, days=30)
                raise Exception(f"API Error {response.status_code}: {response.text}")
            
            data = response.json()
            df = pd.DataFrame(data, columns=[
                "Open Time", "Open", "High", "Low", "Close", "Volume",
                "Close Time", "Quote Asset Volume", "Number of Trades",
                "Taker Buy Base", "Taker Buy Quote", "Ignore"
            ])
            
            # Convert timestamps and prices
            df['Open Time'] = pd.to_datetime(df['Open Time'], unit='ms')
            df = df[["Open Time", "Open", "High", "Low", "Close", "Volume"]].astype({
                "Open": float, "High": float, "Low": float, "Close": float, "Volume": float
            })
            df.set_index('Open Time', inplace=True)
            return df
            
        except Exception as e:
            # Try CoinGecko as fallback for any error
            try:
                print(f"Binance API failed, trying CoinGecko fallback for {symbol}")
                return self.fetch_coingecko_ohlcv(symbol, days=30)
            except:
                raise Exception(f"Failed to fetch data from both Binance and CoinGecko: {str(e)}")
    
    def add_comprehensive_indicators(self, df):
        """Add comprehensive technical indicators"""
        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']
        
        # Momentum Indicators
        df['RSI_14'] = RSIIndicator(close, window=14).rsi()
        df['RSI_21'] = RSIIndicator(close, window=21).rsi()
        df['Stoch_K'] = StochasticOscillator(high, low, close, window=14).stoch()
        df['Stoch_D'] = StochasticOscillator(high, low, close, window=14).stoch_signal()
        df['Williams_R'] = WilliamsRIndicator(high, low, close).williams_r()
        
        # Trend Indicators
        df['EMA_9'] = EMAIndicator(close, window=9).ema_indicator()
        df['EMA_21'] = EMAIndicator(close, window=21).ema_indicator()
        df['EMA_50'] = EMAIndicator(close, window=50).ema_indicator()
        df['SMA_20'] = SMAIndicator(close, window=20).sma_indicator()
        df['SMA_50'] = SMAIndicator(close, window=50).sma_indicator()
        
        # MACD
        macd = MACD(close)
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        df['MACD_Histogram'] = macd.macd_diff()
        
        # ADX and DI
        adx = ADXIndicator(high, low, close)
        df['ADX'] = adx.adx()
        df['DI_Plus'] = adx.adx_pos()
        df['DI_Minus'] = adx.adx_neg()
        
        # Volatility Indicators
        bb = BollingerBands(close, window=20, window_dev=2)
        df['BB_Upper'] = bb.bollinger_hband()
        df['BB_Middle'] = bb.bollinger_mavg()
        df['BB_Lower'] = bb.bollinger_lband()
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle'] * 100
        df['BB_Position'] = (close - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
        
        # Keltner Channels
        kc = KeltnerChannel(high, low, close)
        df['KC_Upper'] = kc.keltner_channel_hband()
        df['KC_Lower'] = kc.keltner_channel_lband()
        df['KC_Middle'] = kc.keltner_channel_mband()
        
        # ATR and volatility measures
        df['ATR'] = AverageTrueRange(high, low, close).average_true_range()
        df['ATR_Percent'] = (df['ATR'] / close) * 100
        
        # Volume Indicators  
        df['Volume_SMA'] = volume.rolling(window=20).mean()
        df['Volume_Ratio'] = volume / df['Volume_SMA']
        df['OBV'] = OnBalanceVolumeIndicator(close, volume).on_balance_volume()
        df['CMF'] = ChaikinMoneyFlowIndicator(high, low, close, volume).chaikin_money_flow()
        
        # Price Action
        df['Body_Size'] = abs(df['Close'] - df['Open']) / df['Open'] * 100
        df['Upper_Wick'] = (df['High'] - np.maximum(df['Open'], df['Close'])) / df['Open'] * 100
        df['Lower_Wick'] = (np.minimum(df['Open'], df['Close']) - df['Low']) / df['Open'] * 100
        df['Total_Range'] = (df['High'] - df['Low']) / df['Open'] * 100
        
        # Support/Resistance levels (simplified)
        df['Pivot'] = (df['High'] + df['Low'] + df['Close']) / 3
        df['R1'] = 2 * df['Pivot'] - df['Low']
        df['S1'] = 2 * df['Pivot'] - df['High']
        
        # Rate of Change
        df['ROC_5'] = ((close / close.shift(5)) - 1) * 100
        df['ROC_14'] = ((close / close.shift(14)) - 1) * 100
        
        df.dropna(inplace=True)
        return df
    
    def analyze_momentum_confluence(self, row):
        """Analyze momentum indicators for confluences"""
        confluences = {'bullish': [], 'bearish': [], 'neutral': []}
        
        # RSI Analysis
        if row['RSI_14'] < 30:
            confluences['bullish'].append({
                'indicator': 'RSI (14)',
                'condition': f"Oversold at {row['RSI_14']:.1f}",
                'implication': "Potential bounce or reversal setup. Watch for bullish divergence or break above 30.",
                'strength': 'Medium',
                'timeframe': 'Short-term'
            })
        elif row['RSI_14'] > 70:
            confluences['bearish'].append({
                'indicator': 'RSI (14)',
                'condition': f"Overbought at {row['RSI_14']:.1f}",
                'implication': "Potential pullback or distribution. Watch for bearish divergence or break below 70.",
                'strength': 'Medium',
                'timeframe': 'Short-term'
            })
        elif 45 <= row['RSI_14'] <= 55:
            confluences['neutral'].append({
                'indicator': 'RSI (14)',
                'condition': f"Neutral at {row['RSI_14']:.1f}",
                'implication': "Balanced momentum. Look for directional break above 55 or below 45.",
                'strength': 'Low',
                'timeframe': 'Short-term'
            })
        
        # Stochastic Analysis
        if row['Stoch_K'] < 20 and row['Stoch_D'] < 20:
            confluences['bullish'].append({
                'indicator': 'Stochastic',
                'condition': f"Both %K ({row['Stoch_K']:.1f}) and %D ({row['Stoch_D']:.1f}) oversold",
                'implication': "Strong oversold condition. Potential reversal when %K crosses above %D.",
                'strength': 'Strong' if row['Stoch_K'] > row['Stoch_D'] else 'Medium',
                'timeframe': 'Short-term'
            })
        elif row['Stoch_K'] > 80 and row['Stoch_D'] > 80:
            confluences['bearish'].append({
                'indicator': 'Stochastic',
                'condition': f"Both %K ({row['Stoch_K']:.1f}) and %D ({row['Stoch_D']:.1f}) overbought",
                'implication': "Strong overbought condition. Potential reversal when %K crosses below %D.",
                'strength': 'Strong' if row['Stoch_K'] < row['Stoch_D'] else 'Medium',
                'timeframe': 'Short-term'
            })
        
        # Williams %R Analysis
        if row['Williams_R'] < -80:
            confluences['bullish'].append({
                'indicator': 'Williams %R',
                'condition': f"Oversold at {row['Williams_R']:.1f}",
                'implication': "Potential buying opportunity. Watch for move above -80 for confirmation.",
                'strength': 'Medium',
                'timeframe': 'Short-term'
            })
        elif row['Williams_R'] > -20:
            confluences['bearish'].append({
                'indicator': 'Williams %R',
                'condition': f"Overbought at {row['Williams_R']:.1f}",
                'implication': "Potential selling pressure. Watch for move below -20 for confirmation.",
                'strength': 'Medium',
                'timeframe': 'Short-term'
            })
        
        return confluences
    
    def analyze_trend_confluence(self, row):
        """Analyze trend indicators for confluences"""
        confluences = {'bullish': [], 'bearish': [], 'neutral': []}
        
        # EMA Alignment
        ema_alignment = "bullish" if row['EMA_9'] > row['EMA_21'] > row['EMA_50'] else "bearish" if row['EMA_9'] < row['EMA_21'] < row['EMA_50'] else "mixed"
        
        if ema_alignment == "bullish":
            confluences['bullish'].append({
                'indicator': 'EMA Alignment',
                'condition': "EMA 9 > EMA 21 > EMA 50",
                'implication': "Strong bullish trend structure. Expect continuation with pullbacks to EMAs as support.",
                'strength': 'Strong',
                'timeframe': 'Medium-term'
            })
        elif ema_alignment == "bearish":
            confluences['bearish'].append({
                'indicator': 'EMA Alignment',
                'condition': "EMA 9 < EMA 21 < EMA 50",
                'implication': "Strong bearish trend structure. Expect continuation with rallies to EMAs as resistance.",
                'strength': 'Strong',
                'timeframe': 'Medium-term'
            })
        
        # Price vs EMAs
        if row['Close'] > row['EMA_21']:
            confluences['bullish'].append({
                'indicator': 'Price vs EMA 21',
                'condition': f"Price {((row['Close']/row['EMA_21']-1)*100):+.2f}% above EMA 21",
                'implication': "Bullish bias maintained. EMA 21 likely to act as dynamic support.",
                'strength': 'Medium',
                'timeframe': 'Short to Medium-term'
            })
        else:
            confluences['bearish'].append({
                'indicator': 'Price vs EMA 21',
                'condition': f"Price {((row['Close']/row['EMA_21']-1)*100):+.2f}% below EMA 21",
                'implication': "Bearish bias maintained. EMA 21 likely to act as dynamic resistance.",
                'strength': 'Medium',
                'timeframe': 'Short to Medium-term'
            })
        
        # MACD Analysis
        if row['MACD'] > row['MACD_Signal'] and row['MACD_Histogram'] > 0:
            confluences['bullish'].append({
                'indicator': 'MACD',
                'condition': "MACD above signal line with positive histogram",
                'implication': "Bullish momentum building. Watch for histogram expansion for stronger moves.",
                'strength': 'Strong' if row['MACD_Histogram'] > 0 else 'Medium',
                'timeframe': 'Medium-term'
            })
        elif row['MACD'] < row['MACD_Signal'] and row['MACD_Histogram'] < 0:
            confluences['bearish'].append({
                'indicator': 'MACD',
                'condition': "MACD below signal line with negative histogram",
                'implication': "Bearish momentum building. Watch for histogram expansion for stronger moves.",
                'strength': 'Strong' if row['MACD_Histogram'] < 0 else 'Medium',
                'timeframe': 'Medium-term'
            })
        
        # ADX Trend Strength
        if row['ADX'] > 25:
            trend_direction = "bullish" if row['DI_Plus'] > row['DI_Minus'] else "bearish"
            confluences[trend_direction].append({
                'indicator': 'ADX Trend Strength',
                'condition': f"Strong trending market (ADX: {row['ADX']:.1f})",
                'implication': f"Strong {trend_direction} trend in place. Expect trend continuation with minor pullbacks.",
                'strength': 'Strong' if row['ADX'] > 40 else 'Medium',
                'timeframe': 'Medium to Long-term'
            })
        elif row['ADX'] < 20:
            confluences['neutral'].append({
                'indicator': 'ADX Trend Strength',
                'condition': f"Weak trending market (ADX: {row['ADX']:.1f})",
                'implication': "Market in consolidation/ranging phase. Look for breakout setups.",
                'strength': 'Medium',
                'timeframe': 'All timeframes'
            })
        
        return confluences
    
    def analyze_volatility_confluence(self, row):
        """Analyze volatility indicators for confluences"""
        confluences = {'bullish': [], 'bearish': [], 'neutral': []}
        
        # Bollinger Bands Analysis
        if row['BB_Position'] < 0.2:
            confluences['bullish'].append({
                'indicator': 'Bollinger Bands',
                'condition': f"Price near lower band (Position: {row['BB_Position']:.2f})",
                'implication': "Potential oversold bounce. Watch for move back toward middle band.",
                'strength': 'Medium',
                'timeframe': 'Short-term'
            })
        elif row['BB_Position'] > 0.8:
            confluences['bearish'].append({
                'indicator': 'Bollinger Bands',
                'condition': f"Price near upper band (Position: {row['BB_Position']:.2f})",
                'implication': "Potential overbought pullback. Watch for move back toward middle band.",
                'strength': 'Medium',
                'timeframe': 'Short-term'
            })
        
        # ATR Analysis
        if row['ATR_Percent'] > 5:
            confluences['neutral'].append({
                'indicator': 'ATR',
                'condition': f"High volatility ({row['ATR_Percent']:.2f}%)",
                'implication': "Elevated volatility suggests increased risk/reward. Use wider stops.",
                'strength': 'Medium',
                'timeframe': 'All timeframes'
            })
        elif row['ATR_Percent'] < 1:
            confluences['neutral'].append({
                'indicator': 'ATR',
                'condition': f"Low volatility ({row['ATR_Percent']:.2f}%)",
                'implication': "Low volatility suggests potential for breakout. Watch for expansion.",
                'strength': 'Medium',
                'timeframe': 'All timeframes'
            })
        
        return confluences
    
    def analyze_volume_confluence(self, row):
        """Analyze volume indicators for confluences"""
        confluences = {'bullish': [], 'bearish': [], 'neutral': []}
        
        # Volume Analysis
        if row['Volume_Ratio'] > 2:
            confluences['neutral'].append({
                'indicator': 'Volume',
                'condition': f"High volume ({row['Volume_Ratio']:.1f}x average)",
                'implication': "Strong institutional interest. Confirms price moves.",
                'strength': 'Strong',
                'timeframe': 'All timeframes'
            })
        elif row['Volume_Ratio'] < 0.5:
            confluences['neutral'].append({
                'indicator': 'Volume',
                'condition': f"Low volume ({row['Volume_Ratio']:.1f}x average)",
                'implication': "Weak participation. Price moves may lack conviction.",
                'strength': 'Medium',
                'timeframe': 'All timeframes'
            })
        
        # CMF Analysis
        if row['CMF'] > 0.2:
            confluences['bullish'].append({
                'indicator': 'Chaikin Money Flow',
                'condition': f"Strong buying pressure (CMF: {row['CMF']:.3f})",
                'implication': "Money flowing into the asset. Supports bullish bias.",
                'strength': 'Medium',
                'timeframe': 'Medium-term'
            })
        elif row['CMF'] < -0.2:
            confluences['bearish'].append({
                'indicator': 'Chaikin Money Flow',
                'condition': f"Strong selling pressure (CMF: {row['CMF']:.3f})",
                'implication': "Money flowing out of the asset. Supports bearish bias.",
                'strength': 'Medium',
                'timeframe': 'Medium-term'
            })
        
        return confluences
    
    def get_comprehensive_analysis(self, symbol="BTCUSDT", interval="15m"):
        """Get comprehensive trading analysis"""
        try:
            # Fetch data
            df = self.fetch_binance_ohlcv(symbol, interval)
            df = self.add_comprehensive_indicators(df)
            
            if df.empty:
                return {"error": "No data available"}
            
            # Get latest row
            latest = df.iloc[-1]
            
            # Analyze confluences
            momentum = self.analyze_momentum_confluence(latest)
            trend = self.analyze_trend_confluence(latest)
            volatility = self.analyze_volatility_confluence(latest)
            volume = self.analyze_volume_confluence(latest)
            
            # Combine all confluences
            all_confluences = {
                'bullish': momentum['bullish'] + trend['bullish'] + volatility['bullish'] + volume['bullish'],
                'bearish': momentum['bearish'] + trend['bearish'] + volatility['bearish'] + volume['bearish'],
                'neutral': momentum['neutral'] + trend['neutral'] + volatility['neutral'] + volume['neutral']
            }
            
            # Generate overall signal
            bullish_count = len(all_confluences['bullish'])
            bearish_count = len(all_confluences['bearish'])
            
            if bullish_count >= self.confluence_threshold and bullish_count > bearish_count:
                overall_signal = "BULLISH"
                signal_strength = "Strong" if bullish_count >= 5 else "Medium"
            elif bearish_count >= self.confluence_threshold and bearish_count > bullish_count:
                overall_signal = "BEARISH"
                signal_strength = "Strong" if bearish_count >= 5 else "Medium"
            else:
                overall_signal = "NEUTRAL"
                signal_strength = "Weak"
            
            return {
                "symbol": symbol,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "current_price": latest['Close'],
                "overall_signal": overall_signal,
                "signal_strength": signal_strength,
                "confluence_counts": {
                    "bullish": bullish_count,
                    "bearish": bearish_count,
                    "neutral": len(all_confluences['neutral'])
                },
                "confluences": all_confluences,
                "key_levels": {
                    "resistance": latest['R1'],
                    "support": latest['S1'],
                    "pivot": latest['Pivot']
                },
                "technical_snapshot": {
                    "RSI_14": latest['RSI_14'],
                    "MACD": latest['MACD'],
                    "ADX": latest['ADX'],
                    "ATR_Percent": latest['ATR_Percent'],
                    "BB_Position": latest['BB_Position']
                }
            }
            
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}

    def format_confluence_analysis(self, analysis):
        """Format confluence analysis for display"""
        if "error" in analysis:
            return f"❌ {analysis['error']}"
        
        output = []
        output.append(f"📊 **Analysis for {analysis['symbol']}**")
        output.append(f"⏰ Generated: {analysis['timestamp']}")
        output.append(f"💰 Current Price: ${analysis['current_price']:.6f}")
        output.append("")
        
        # Overall Signal
        signal_emoji = "🟢" if analysis['overall_signal'] == "BULLISH" else "🔴" if analysis['overall_signal'] == "BEARISH" else "🟡"
        output.append(f"{signal_emoji} **Overall Signal: {analysis['overall_signal']} ({analysis['signal_strength']})**")
        output.append("")
        
        # Confluence Counts
        counts = analysis['confluence_counts']
        output.append(f"📈 Bullish Confluences: {counts['bullish']}")
        output.append(f"📉 Bearish Confluences: {counts['bearish']}")
        output.append(f"⚪ Neutral Confluences: {counts['neutral']}")
        output.append("")
        
        # Key Levels
        levels = analysis['key_levels']
        output.append("🎯 **Key Levels:**")
        output.append(f"   Resistance: ${levels['resistance']:.6f}")
        output.append(f"   Pivot: ${levels['pivot']:.6f}")
        output.append(f"   Support: ${levels['support']:.6f}")
        output.append("")
        
        # Technical Snapshot
        tech = analysis['technical_snapshot']
        output.append("📋 **Technical Snapshot:**")
        output.append(f"   RSI (14): {tech['RSI_14']:.1f}")
        output.append(f"   MACD: {tech['MACD']:.6f}")
        output.append(f"   ADX: {tech['ADX']:.1f}")
        output.append(f"   ATR%: {tech['ATR_Percent']:.2f}%")
        output.append(f"   BB Position: {tech['BB_Position']:.3f}")
        output.append("")
        
        # Detailed Confluences
        confluences = analysis['confluences']
        
        if confluences['bullish']:
            output.append("🟢 **Bullish Confluences:**")
            for conf in confluences['bullish']:
                output.append(f"   • **{conf['indicator']}** ({conf['strength']}, {conf['timeframe']})")
                output.append(f"     {conf['condition']}")
                output.append(f"     {conf['implication']}")
                output.append("")
        
        if confluences['bearish']:
            output.append("🔴 **Bearish Confluences:**")
            for conf in confluences['bearish']:
                output.append(f"   • **{conf['indicator']}** ({conf['strength']}, {conf['timeframe']})")
                output.append(f"     {conf['condition']}")
                output.append(f"     {conf['implication']}")
                output.append("")
        
        if confluences['neutral']:
            output.append("⚪ **Neutral Confluences:**")
            for conf in confluences['neutral']:
                output.append(f"   • **{conf['indicator']}** ({conf['strength']}, {conf['timeframe']})")
                output.append(f"     {conf['condition']}")
                output.append(f"     {conf['implication']}")
                output.append("")
        
        return "\n".join(output)
