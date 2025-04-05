# Streamlit ile İlk 5 Major Coin Teknik Analiz Paneli (Günlük, YFinance) — Test Sürümü

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# Basit parola kontrolü
st.set_page_config(page_title="Kripto Sinyal Paneli (Test)", layout="wide")
password = st.text_input("🔐 Giriş için parolanızı girin:", type="password")
if password != "berlinharunHh_":
    st.warning("⚠️ Erişim reddedildi. Doğru parolayı girin.")
    st.stop()

# YFinance sembolleri
COIN_MAP = {
    'BTC': 'BTC-USD',
    'ETH': 'ETH-USD',
    'BNB': 'BNB-USD',
    'SOL': 'SOL-USD',
    'XRP': 'XRP-USD'
}

def get_ohlcv_from_yfinance(symbol, period='90d', interval='1d'):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        df = df[['Close', 'Volume']].rename(columns={'Close': 'close', 'Volume': 'volume'})
        return df
    except Exception as e:
        st.error(f"{symbol} veri çekme hatası: {str(e)}")
        return pd.DataFrame()

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal, adjust=False).mean()
    return macd, macd_signal

def calculate_signal(df):
    if df.empty or len(df) < 50:
        return 'Data Error'

    df['EMA20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['RSI'] = compute_rsi(df['close'])
    df['MACD'], df['MACDSignal'] = compute_macd(df['close'])
    df['VolMA20'] = df['volume'].rolling(window=20).mean()

    latest = df.iloc[-1]
    if (
        latest['close'] > latest['EMA20'] > latest['EMA50']
        and latest['MACD'] > latest['MACDSignal']
        and latest['volume'] > latest['VolMA20']
        and 40 < latest['RSI'] < 70
    ):
        return 'LONG'
    elif latest['RSI'] < 30 and latest['MACD'] > latest['MACDSignal']:
        return 'LONG'
    elif latest['RSI'] > 70 and latest['MACD'] < latest['MACDSignal']:
        return 'SHORT'
    else:
        return 'HOLD'

# İlk 5 major coin için sinyal üret
TOP_COINS = list(COIN_MAP.keys())

st.title("🧪 İlk 5 Major Coin Günlük Teknik Sinyal Paneli (YFinance)")

results = []
for symbol in TOP_COINS:
    try:
        df = get_ohlcv_from_yfinance(COIN_MAP[symbol])
        signal = calculate_signal(df)
        results.append({
            'Coin': symbol,
            'Last Close ($)': round(df['close'].iloc[-1], 2) if not df.empty else 'N/A',
            'Signal': signal
        })
    except Exception as e:
        results.append({'Coin': symbol, 'Signal': f'Error: {str(e)}'})

st.dataframe(pd.DataFrame(results))
