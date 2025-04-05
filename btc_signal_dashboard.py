# Streamlit ile İlk 5 Major Coin Teknik Analiz Paneli (Günlük, Binance API) — Test Sürümü

import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime

# Basit parola kontrolü
st.set_page_config(page_title="Kripto Sinyal Paneli (Test)", layout="wide")
password = st.text_input("🔐 Giriş için parolanızı girin:", type="password")
if password != "berlinharunHh_":
    st.warning("⚠️ Erişim reddedildi. Doğru parolayı girin.")
    st.stop()

BASE_URL = 'https://api.binance.com'

def get_klines(symbol, interval='1d', limit=100):
    url = f"{BASE_URL}/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    response = requests.get(url, params=params)
    try:
        data = response.json()
        st.write(f"{symbol} API yanıtı:", data[:1])
        if isinstance(data, dict) and "code" in data:
            return pd.DataFrame()
        df = pd.DataFrame(data, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'])
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        return df[['close', 'volume']]
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

# Yalnızca ilk 5 major coin ile test
TOP_COINS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']

st.title("🧪 İlk 5 Major Coin Günlük Teknik Sinyal Paneli (TEST)")

results = []
for symbol in TOP_COINS:
    try:
        df = get_klines(symbol)
        time.sleep(0.5)  # Rate limit koruması
        signal = calculate_signal(df)
        results.append({
            'Coin': symbol.replace('USDT', ''),
            'Last Close ($)': round(df['close'].iloc[-1], 2) if not df.empty else 'N/A',
            'Signal': signal
        })
    except Exception as e:
        results.append({'Coin': symbol.replace('USDT', ''), 'Signal': f'Error: {str(e)}'})

st.dataframe(pd.DataFrame(results))
