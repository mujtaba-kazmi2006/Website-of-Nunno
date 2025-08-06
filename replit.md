# Overview

Nunno AI is a comprehensive finance assistant application built with Streamlit that provides personal financial education, trading analysis, and market insights. The application features a modern dark-themed multi-page interface designed to help beginners learn investing and trading through AI-powered conversations, advanced technical analysis with interactive charts, tokenomics evaluation, and real-time market news. Built by Mujtaba Kazmi, the system positions itself as "Numinous Nexus AI" - a central hub of financial knowledge that makes complex financial concepts accessible to newcomers.

## Recent Updates (August 2025)
- ✅ **Professional Dark Mode**: Implemented cohesive dark theme across entire application with teal accents (#00d4aa)
- ✅ **Interactive Charts**: Added comprehensive 4-panel technical analysis charts (Price/EMAs, RSI, MACD, Volume)
- ✅ **API Fallback System**: Implemented CoinGecko fallback when Binance API is geo-restricted
- ✅ **Enhanced UI/UX**: Gradient buttons, hover effects, and professional trading terminal aesthetic

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Framework**: Streamlit with multi-page application structure
- **UI Pattern**: Sidebar navigation with page-based routing
- **State Management**: Streamlit session state for user profile and conversation history
- **User Experience**: Welcome screen with mandatory profile setup before accessing features

## Core Application Components

### Main Application (`app.py`)
- **Purpose**: Entry point with profile setup and welcome interface
- **Session Management**: Handles user profile initialization and validation
- **Navigation**: Controls access to other pages based on profile completion status

### AI Chat System (`pages/1_🔮_AI_Chat.py`)
- **AI Integration**: OpenRouter API for conversational AI capabilities
- **Conversation Management**: History tracking with configurable message limits (20 messages)
- **Personality**: Custom system prompt defining "Nunno" AI assistant persona focused on financial education
- **Context Awareness**: Personalized responses based on user name and age

### Technical Analysis Engine (`betterpredictormodule.py`)
- **Data Sources**: Binance API (primary) with CoinGecko fallback for global accessibility
- **Technical Indicators**: Comprehensive suite including RSI, MACD, Bollinger Bands, Stochastic Oscillator, Williams %R, and volume indicators
- **Analysis Strategy**: Confluence-based signal generation requiring multiple indicator agreement
- **Visualization**: Professional 4-panel interactive Plotly charts with dark theme:
  - Candlestick price chart with EMAs and Bollinger Bands
  - RSI panel with overbought/oversold levels
  - MACD panel with signal line and histogram
  - Volume analysis panel

### Tokenomics Analysis (`pages/3_💰_Tokenomics.py`)
- **Data Provider**: CoinGecko API for cryptocurrency market data
- **Investment Metrics**: CAGR calculation, volatility analysis, and risk assessment
- **Symbol Matching**: Fuzzy string matching for cryptocurrency symbol resolution
- **Historical Analysis**: 365-day price history for trend and performance evaluation

### Market News Integration (`pages/4_📰_Market_News.py`)
- **News Aggregation**: NewsAPI integration for financial news from major outlets
- **Content Filtering**: Focused on finance, crypto, and market-relevant topics
- **Source Diversity**: Multiple financial news sources including CNBC, Bloomberg, Reuters
- **Real-time Updates**: Cached news feeds with configurable refresh intervals

## Data Management
- **Caching Strategy**: Streamlit's built-in caching for API responses and computational results
- **Session Persistence**: User profile and conversation history stored in session state
- **API Rate Limiting**: TTL-based caching to minimize external API calls

## Security and Configuration
- **API Key Management**: Environment variable configuration with fallback defaults
- **Input Validation**: User input sanitization and error handling
- **Error Handling**: Comprehensive exception handling for external API failures

# External Dependencies

## APIs and Services
- **OpenRouter API**: Primary AI conversation engine with custom financial assistant persona
- **Binance API**: Real-time cryptocurrency market data and OHLCV feeds
- **CoinGecko API**: Historical cryptocurrency prices and market information
- **NewsAPI**: Financial news aggregation from major market news sources

## Python Libraries
- **Streamlit**: Web application framework and UI components
- **Plotly**: Interactive charting and data visualization
- **Technical Analysis (ta)**: Comprehensive technical indicator calculations
- **Pandas/NumPy**: Data manipulation and numerical computations
- **Requests**: HTTP client for API integrations
- **FuzzyWuzzy**: String matching for cryptocurrency symbol resolution

## Development Dependencies
- **Threading**: Background processing capabilities (legacy from desktop version)
- **Text-to-Speech (pyttsx3)**: Audio output functionality (legacy component)