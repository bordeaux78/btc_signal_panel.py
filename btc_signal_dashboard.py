# Streamlit ile İlk 51 Coin Teknik Analiz Paneli (Günlük, Binance API) — Şifreli Erişimli

import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime
from binance.client import Client
from binance.exceptions import BinanceAPIException

# Basit parola kontrolü
st.set_page_config(page_title="Kripto Sinyal Paneli", layout="wide")
password = st.text_input("🔐 Giriş için parolanızı girin:", type="password")
if password != "berlinharunHh_":
    st.warning("⚠️ Erişim reddedildi. Doğru parolayı girin.")
    st.stop()

# Binance API Key (Kamuya açık erişimle çalışıyoruz, özel API key gerekmez)
BASE_URL = 'https://api.binance.com'

# Teknik analiz fonksiyonları

def get_klines(symbol, interval='1d', limit=100):
    url = f"{BASE_URL}/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    response = requests.get(url, params=params)
    data = response.json()
    df = pd.DataFrame(data, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'])
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)
    return df[['close', 'volume']]


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

# İlk 51 coin listesi (USDT pariteleri için)
TOP_50_SYMBOLS = [
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT',
    'ADAUSDT', 'AVAXUSDT', 'DOTUSDT', 'LINKUSDT', 'TRXUSDT', 'MATICUSDT',
    'LTCUSDT', 'BCHUSDT', 'UNIUSDT', 'XLMUSDT', 'ETCUSDT', 'ICPUSDT',
    'FILUSDT', 'HBARUSDT', 'VETUSDT', 'SANDUSDT', 'MANAUSDT', 'AAVEUSDT',
    'EOSUSDT', 'THETAUSDT', 'XTZUSDT', 'NEARUSDT', 'FTMUSDT', 'RUNEUSDT',
    'GRTUSDT', 'EGLDUSDT', 'CAKEUSDT', 'CHZUSDT', 'ENJUSDT', 'ZILUSDT',
    'KSMUSDT', 'COMPUSDT', 'YFIUSDT', 'CRVUSDT', '1INCHUSDT', 'SNXUSDT',
    'RENUSDT', 'ZRXUSDT', 'OMGUSDT', 'BATUSDT', 'ANKRUSDT', 'ALGOUSDT',
    'FLOWUSDT', 'ARUSDT', 'MKRUSDT'
]

st.title("📈 İlk 51 Coin Günlük Teknik Sinyal Paneli")

st.markdown("""
<style>
thead tr th:first-child {display:none}
tbody th {display:none}
</style>
""", unsafe_allow_html=True)

results = []
for symbol in TOP_50_SYMBOLS:
    try:
        df = get_klines(symbol)
        signal = calculate_signal(df)
        results.append({
            'Coin': symbol.replace('USDT', ''),
            'Last Close ($)': round(df['close'].iloc[-1], 2),
            'RSI': round(df['RSI'].iloc[-1], 2),
            'MACD': round(df['MACD'].iloc[-1], 2),
            'MACD Signal': round(df['MACDSignal'].iloc[-1], 2),
            'Trend': 'Bullish' if df['close'].iloc[-1] > df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1] else 'Bearish',
            'Volume Check': 'High' if df['volume'].iloc[-1] > df['VolMA20'].iloc[-1] else 'Low',
            'Signal': signal
        })
    except Exception as e:
        results.append({'Coin': symbol.replace('USDT', ''), 'Signal': f'Error: {str(e)}'})

result_df = pd.DataFrame(results)
st.dataframe(result_df.sort_values(by='Coin').reset_index(drop=True))
