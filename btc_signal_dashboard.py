# Streamlit ile İlk 51 Coin Teknik Analiz Paneli (Günlük, YFinance) — Tam Sürüm

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# Basit parola kontrolü
st.set_page_config(page_title="Kripto Sinyal Paneli", layout="wide")
password = st.text_input("🔐 Giriş için parolanızı girin:", type="password")
if password != "berlinharunHh_":
    st.warning("⚠️ Erişim reddedildi. Doğru parolayı girin.")
    st.stop()

# İlk 50 coin + MKR
TOP_COINS = [
    'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 'DOT', 'TRX',
    'LINK', 'MATIC', 'LTC', 'BCH', 'UNI', 'XLM', 'ATOM', 'ETC', 'HBAR', 'APT',
    'FIL', 'VET', 'ICP', 'SAND', 'MANA', 'INJ', 'AAVE', 'EGLD', 'THETA', 'XTZ',
    'RUNE', 'NEAR', 'GRT', 'FLOW', 'FTM', 'CHZ', 'CAKE', 'XMR', 'ZEC', 'DYDX',
    'CRV', 'SNX', 'ENS', 'LDO', 'CFX', 'AR', 'KAVA', 'ANKR', 'GMX', 'COMP', 'MKR'
]

COIN_MAP = {symbol: f"{symbol}-USD" for symbol in TOP_COINS}

# Veri çekme

def get_ohlcv_from_yfinance(symbol, period='90d', interval='1d'):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        df = df[['Close', 'Volume']].rename(columns={'Close': 'close', 'Volume': 'volume'})
        df = df.reset_index(drop=True)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        return df
    except Exception as e:
        st.error(f"{symbol} veri çekme hatası: {str(e)}")
        return pd.DataFrame()

# RSI

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# MACD

def compute_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal, adjust=False).mean()
    return macd, macd_signal

# Sinyal hesaplama

def calculate_signal(df):
    if df.empty or len(df) < 50:
        return 'Data Error'

    df['EMA20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['RSI'] = compute_rsi(df['close'])
    df['MACD'], df['MACDSignal'] = compute_macd(df['close'])
    df['VolMA20'] = df['volume'].rolling(window=20).mean()

    try:
        close = df['close'].iloc[-1].item()
        ema20 = df['EMA20'].iloc[-1].item()
        ema50 = df['EMA50'].iloc[-1].item()
        macd = df['MACD'].iloc[-1].item()
        macd_signal = df['MACDSignal'].iloc[-1].item()
        rsi = df['RSI'].iloc[-1].item()
        volume = df['volume'].iloc[-1].item()
        volma = df['VolMA20'].iloc[-1].item()

        if close > ema20 > ema50 and macd > macd_signal and volume > volma and 40 < rsi < 70:
            return '🟢 LONG'
        elif rsi < 30 and macd > macd_signal:
            return '🟢 LONG'
        elif rsi > 70 and macd < macd_signal:
            return '🔴 SHORT'
        else:
            return '⚪ HOLD'
    except Exception as e:
        return f'Error: {str(e)}'

# Arayüz başlığı
st.title("📊 İlk 51 Coin Günlük Teknik Sinyal Paneli")

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
