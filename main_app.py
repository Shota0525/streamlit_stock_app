# ライブラリをインポート
import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands


# 各関数を定義 #################################################################################################################################
# 株価を取得する関数
def get_stock_price(ticker, period, interval):
    data = yf.download(ticker, period = period, interval = interval)
    return data


# 株価データを描画する関数
def plot_stock_price(ticker, period, title):
    data = get_stock_price(ticker, period = period, interval = '1d')
    # プロットの区切りを設定
    fig = make_subplots(rows=1, cols=1, shared_xaxes=True, vertical_spacing=0.03)
    # 株価データと移動曲線を描画
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='original'))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=25).mean(), name='MA25', line=dict(color='lightcoral')))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=50).mean(), name='MA50', line=dict(color='lightblue')))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=75).mean(), name='MA75', line=dict(color='lightsalmon')))
    # ボリンジャーバンドを描画
    indicator_bb = BollingerBands(close=data["Close"], window=20, window_dev=2)
    fig.add_trace(go.Scatter(x=data.index, y=indicator_bb.bollinger_hband(), name='Upper BB', line=dict(color='palevioletred', dash='dash')))
    fig.add_trace(go.Scatter(x=data.index, y=indicator_bb.bollinger_lband(), name='Lower BB', line=dict(color='palevioletred', dash='dash')))

    fig.update_layout(title={'text': title, 'x': 0.5, 'y': 0.8, 'xanchor': 'center', 'yanchor': 'top'}, xaxis_rangeslider_visible=False, showlegend=False)
    return fig


# VIXを描画する関数
def plot_vix(period):
    data = get_stock_price('^VIX', period = period, interval = '1d')
    # プロットの区切りを設定
    fig = make_subplots(rows=1, cols=1, shared_xaxes=True, vertical_spacing=0.03)
    # 指数データと移動曲線を描画
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='original'))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=25).mean(), name='MA25', line=dict(color='lightcoral')))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=50).mean(), name='MA50', line=dict(color='lightblue')))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=75).mean(), name='MA75', line=dict(color='lightsalmon')))
    # 20と30の水平線を追加 
    fig.add_shape(type='line', x0=data.index[0], x1=data.index[-1], y0=20, y1=20, line=dict(color='palevioletred', width=2, dash='dash')) 
    fig.add_shape(type='line', x0=data.index[0], x1=data.index[-1], y0=30, y1=30, line=dict(color='red', width=2, dash='dash'))

    fig.update_layout(title={'text': 'VIX指数', 'x': 0.5, 'y': 0.8, 'xanchor': 'center', 'yanchor': 'top'}, xaxis_rangeslider_visible=False, showlegend=False)
    return fig



###############################################################################################################################################


# アプリ画面構成 #######################################################################
period_list = ['6mo', '1y', '2y']
period = st.selectbox('表示期間', period_list)
st.divider()

# 株価指標を表示
st.title("株価関連指数")
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(plot_stock_price('^DJI', period, 'ダウ平均'))
    st.plotly_chart(plot_stock_price('^GSPC', period, 'S&P500指数'))
with col2:
    st.plotly_chart(plot_stock_price('^IXIC', period, 'ナスダック総合指数'))
    st.plotly_chart(plot_stock_price('^N225', period, '日経平均株価'))
    
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(plot_vix(period))
    st.plotly_chart(plot_stock_price('^TNX', period, '米10年国債'))
with col2:
    st.plotly_chart(plot_stock_price('^SOX', period, 'フィラデルフィア半導体指数（SOX）'))
    st.plotly_chart(plot_stock_price('^XAU', period, '金 現物'))
st.divider()


# 為替指数を表示
st.title("為替指数")
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(plot_stock_price('USDJPY=X', period, '米ドル/日本円'))
with col2:
    st.plotly_chart(plot_stock_price('EURJPY=X', period, 'ユーロ/日本円'))
st.divider()


# グローバルサウスを表示
st.title("グローバルサウス（ ETF ）")
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(plot_stock_price('EPI', period, 'インド（EPI）'))
    st.plotly_chart(plot_stock_price('VNM', period, 'ベトナム（VNM）'))
with col2:
    st.plotly_chart(plot_stock_price('TUR', period, 'トルコ（TUR）'))
    st.plotly_chart(plot_stock_price('EWW', period, 'メキシコ（EWW）'))
st.divider()


# 暗号資産を表示
st.title("暗号資産")
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(plot_stock_price('BTC-USD', period, 'ビットコイン（ USD ）'))
with col2:
    st.plotly_chart(plot_stock_price('ETH-USD', period, 'イーサリアム（ USD ）'))

#######################################################################################





