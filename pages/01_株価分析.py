# ライブラリをインポート
import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands


# 株価を取得したい銘柄を指定
################
ticker = '^N225'
period = '1y'
interval = '1d'
################


# 株価データを描画する関数
def plot_stock_price(ticker, period, interval):
    data = yf.download(ticker, period = period, interval = interval)
    # プロットの区切りを設定
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.5, 0.25, 0.25])

    # 1段目の株価の主データを描画
    fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name='original'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=50).mean(), name='MA50', line=dict(color='lightblue')), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=75).mean(), name='MA75', line=dict(color='lightsalmon')), row=1, col=1)

    # ボリンジャーバンドも描画
    indicator_bb = BollingerBands(close=data["Close"], window=20, window_dev=2)
    fig.add_trace(go.Scatter(x=data.index, y=indicator_bb.bollinger_hband(), name='Upper BB', line=dict(color='palevioletred', dash='dash')), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=indicator_bb.bollinger_lband(), name='Lower BB', line=dict(color='palevioletred', dash='dash')), row=1, col=1)

    # 2段目にRSIを描画
    rsi = RSIIndicator(data['Close']).rsi()
    fig.add_trace(go.Scatter(x=data.index, y=rsi, name='RSI', line=dict(color='rosybrown')), row=2, col=1)

    # 3段目に取引量を描画
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'], name='Volume', marker=dict(color='sandybrown')), row=3, col=1)

    fig.update_layout(xaxis_rangeslider_visible=False)
    return fig
    


# StreamlitでPlotlyグラフを表示
st.plotly_chart(plot_stock_price(ticker, period, interval))

