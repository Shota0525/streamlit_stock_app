# ライブラリをインポート
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ta.volatility import BollingerBands

# 各関数を定義 #################################################################################################################################
# 株価を取得する関数
def get_stock_price(ticker, period, interval):
    # 最新yfinance対応版: MultiIndex解除
    data = yf.download(ticker, period=period, interval=interval, progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data

# 株価データを描画する関数
def plot_stock_price(ticker, period, title):
    data = get_stock_price(ticker, period=period, interval='1d')
    if data.empty: return go.Figure()

    fig = make_subplots(rows=1, cols=1, shared_xaxes=True, vertical_spacing=0.03)
    
    # 色味は維持
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='original'))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=25).mean(), name='MA25', line=dict(color='lightcoral')))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=50).mean(), name='MA50', line=dict(color='lightblue')))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=75).mean(), name='MA75', line=dict(color='lightsalmon')))

    indicator_bb = BollingerBands(close=data["Close"], window=20, window_dev=2)
    fig.add_trace(go.Scatter(x=data.index, y=indicator_bb.bollinger_hband(), name='Upper BB', line=dict(color='palevioletred', dash='dash')))
    fig.add_trace(go.Scatter(x=data.index, y=indicator_bb.bollinger_lband(), name='Lower BB', line=dict(color='palevioletred', dash='dash')))

    # タイトル中央寄せ
    fig.update_layout(
        title={'text': title, 'x': 0.5, 'xanchor': 'center'},
        xaxis_rangeslider_visible=False, 
        showlegend=False
    )
    return fig

# VIXを描画する関数
def plot_vix(period):
    data = get_stock_price('^VIX', period=period, interval='1d')
    if data.empty: return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='original'))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=25).mean(), name='MA25', line=dict(color='lightcoral')))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=50).mean(), name='MA50', line=dict(color='lightblue')))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=75).mean(), name='MA75', line=dict(color='lightsalmon')))

    fig.add_hline(y=20, line_dash="dash", line_color="palevioletred", line_width=2) 
    fig.add_hline(y=30, line_dash="dash", line_color="red", line_width=2)

    # タイトル中央寄せ
    fig.update_layout(
        title={'text': 'VIX指数', 'x': 0.5, 'xanchor': 'center'},
        xaxis_rangeslider_visible=False, 
        showlegend=False
    )
    return fig

# アプリ画面構成 #######################################################################
# index=0 で 6mo をデフォルトに設定
period = st.selectbox('表示期間', ['6mo', '1y', '2y'], index=0)
st.divider()

# 株価指標を表示
st.header("株価関連指数")

tab1, tab2 = st.tabs(["米国", "日本"])
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(plot_stock_price('^DJI', period, 'ダウ平均'), use_container_width=True)
        st.plotly_chart(plot_stock_price('^IXIC', period, 'ナスダック総合指数'), use_container_width=True)
    with col2:
        st.plotly_chart(plot_stock_price('^GSPC', period, 'S&P500指数'), use_container_width=True)
with tab2:
    st.plotly_chart(plot_stock_price('^N225', period, '日経平均株価'), use_container_width=True)

st.divider()
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(plot_vix(period), use_container_width=True)
    st.plotly_chart(plot_stock_price('^TNX', period, '米10年国債利回り（％）'), use_container_width=True)
    st.plotly_chart(plot_stock_price('^SOX', period, 'フィラデルフィア半導体指数（SOX）'), use_container_width=True)
with col2:
    st.plotly_chart(plot_stock_price('CL=F', period, 'WTI原油'), use_container_width=True)
    st.plotly_chart(plot_stock_price('1328.T', period, '金 投信'), use_container_width=True)
    st.plotly_chart(plot_stock_price('1693.T', period, '銅 投信'), use_container_width=True)


# 為替指数を表示
st.header("為替指数")
if 'show_exchange_rate' not in st.session_state:
    st.session_state['show_exchange_rate'] = False
    
col1, col2 = st.columns(2)
with col1:
    if st.button("表示", type="primary", use_container_width=True, key="show_exchange_rate_button"):
        st.session_state['show_exchange_rate'] = True
with col2:
    if st.button("非表示", type="secondary", use_container_width=True, key="hide_exchange_rate_button"):
        st.session_state['show_exchange_rate'] = False

if st.session_state['show_exchange_rate']:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(plot_stock_price('USDJPY=X', period, '米ドル/日本円'))
        st.plotly_chart(plot_stock_price('GBPJPY=X', period, 'ポンド/日本円'))
    with col2:
        st.plotly_chart(plot_stock_price('EURJPY=X', period, 'ユーロ/日本円'))
        st.plotly_chart(plot_stock_price('CNYJPY=X', period, '人民元/日本円'))
st.divider()


# 暗号資産を表示
st.header("暗号資産")
if 'show_crypto' not in st.session_state:
    st.session_state['show_crypto'] = False
    
col1, col2 = st.columns(2)
with col1:
    if st.button("表示", type="primary", use_container_width=True, key="show_crypto_button"):
        st.session_state['show_crypto'] = True
with col2:
    if st.button("非表示", type="secondary", use_container_width=True, key="hide_crypto_button"):
        st.session_state['show_crypto'] = False

if st.session_state['show_crypto']:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(plot_stock_price('BTC-USD', period, 'ビットコイン（USD）'))
        st.plotly_chart(plot_stock_price('ETH-USD', period, 'イーサリアム（USD）'))
    with col2:
        st.plotly_chart(plot_stock_price('XRP-USD', period, 'リップル（USD）'))
        st.plotly_chart(plot_stock_price('SOL-USD', period, 'ソラナ（USD）'))
st.divider()


# グローバルサウスを表示
st.header("Global South Chart（グローバルサウス）")
if 'show_global_south' not in st.session_state:
    st.session_state['show_global_south'] = False
    
col1, col2 = st.columns(2)
with col1:
    if st.button("表示", type="primary", use_container_width=True):
        st.session_state['show_global_south'] = True
with col2:
    if st.button("非表示", type="secondary", use_container_width=True):
        st.session_state['show_global_south'] = False
        
if st.session_state['show_global_south']:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(plot_stock_price('EPI', period, 'インド（EPI）'))
        st.plotly_chart(plot_stock_price('VNM', period, 'ベトナム（VNM）'))
    with col2:
        st.plotly_chart(plot_stock_price('TUR', period, 'トルコ（TUR）'))
        st.plotly_chart(plot_stock_price('EWW', period, 'メキシコ（EWW）'))
st.divider()
#######################################################################################
