import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go

# --- Config ---
st.set_page_config(page_title="AlgoTrading Intraday", layout="wide")
st.title("📈 My 1st Algo Trading Dashboard")
st.markdown("Strategy: **Mean Reversion (BB + RSI)**")

# --- Sidebar ---
st.sidebar.header("Settings")
symbol = st.sidebar.text_input("Ticker", value="AAPL")
timeframe = st.sidebar.selectbox("Timeframe", ['1m', '5m', '15m'], index=1)
days = st.sidebar.slider("Days Back", 1, 30, 7)

# --- Data ---
@st.cache_data
def load_data(s, p, i):
    return yf.download(s, period=f"{p}d", interval=i)

data = load_data(symbol, days, timeframe)

if not data.empty:
    df = data.copy()
    # Indicators
    bb = ta.bbands(df['Close'], length=20, std=2.0)
    df['BB_L'] = bb.iloc[:, 0]
    df['BB_U'] = bb.iloc[:, 2]
    df['RSI'] = ta.rsi(df['Close'], length=2)
    
    # Signals
    df['Signal'] = 0
    df.loc[(df['Close'] < df['BB_L']) & (df['RSI'] < 10), 'Signal'] = 1
    df.loc[(df['Close'] > df['BB_U']) & (df['RSI'] > 90), 'Signal'] = -1
    
    # Simple Backtest
    df['Return'] = df['Close'].pct_change()
    df['Strategy_Return'] = df['Signal'].shift(1) * df['Return']
    df['Cum_Return'] = (1 + df['Strategy_Return'].fillna(0)).cumprod()

    # Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Return", f"{(df['Cum_Return'].iloc[-1]-1)*100:.2f}%")
    c2.metric("Win Rate", f"{(len(df[df['Strategy_Return']>0])/len(df[df['Strategy_Return']!=0])*100 if len(df[df['Strategy_Return']!=0])>0 else 0):.1f}%")
    c3.metric("Trades", len(df[df['Signal'] != 0]))

    # Chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Price'))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_U'], name='BB Upper', line=dict(dash='dash', color='gray')))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_L'], name='BB Lower', line=dict(dash='dash', color='gray')))
    
    buys = df[df['Signal'] == 1]
    sells = df[df['Signal'] == -1]
    fig.add_trace(go.Scatter(x=buys.index, y=buys['Close'], mode='markers', name='Buy', marker=dict(symbol='triangle-up', size=10, color='green')))
    fig.add_trace(go.Scatter(x=sells.index, y=sells['Close'], mode='markers', name='Sell', marker=dict(symbol='triangle-down', size=10, color='red')))
    
    fig.update_layout(template="plotly_dark", height=600)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("No data found.")
