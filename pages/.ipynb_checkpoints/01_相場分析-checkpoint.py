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


# 各関数を定義 #################################################################################################################################
# 株価を取得する関数
def get_stock_price(ticker, period, interval):
    data = yf.download(ticker, period = period, interval = interval)
    return data


# 株価データを描画する関数
def plot_stock_price(ticker, period, interval, title):
    data = get_stock_price(ticker, period = period, interval = interval)
    # プロットの区切りを設定
    fig = make_subplots(rows=1, cols=1, shared_xaxes=True, vertical_spacing=0.03)

    # 株価データと移動曲線を描画
    fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name='original', increasing_line_color='tomato', decreasing_line_color='cornflowerblue'))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=25).mean(), name='MA25', line=dict(color='lightcoral')))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=50).mean(), name='MA50', line=dict(color='lightblue')))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=75).mean(), name='MA75', line=dict(color='lightsalmon')))

    # ボリンジャーバンドも描画
    indicator_bb = BollingerBands(close=data["Close"], window=20, window_dev=2)
    fig.add_trace(go.Scatter(x=data.index, y=indicator_bb.bollinger_hband(), name='Upper BB', line=dict(color='palevioletred', dash='dash')))
    fig.add_trace(go.Scatter(x=data.index, y=indicator_bb.bollinger_lband(), name='Lower BB', line=dict(color='palevioletred', dash='dash')))

    fig.update_layout(title={'text': title, 'x': 0.5, 'y': 0.8, 'xanchor': 'center', 'yanchor': 'top'}, xaxis_rangeslider_visible=False, showlegend=False)
    return fig


# RSIを描画する関数
def plot_stock_rsi(ticker, period, interval):
    data = get_stock_price(ticker, period = period, interval = interval)
    # プロットの区切りを設定
    fig = make_subplots(rows=1, cols=1, shared_xaxes=True, vertical_spacing=0.03)
    # RSIを描画
    rsi = RSIIndicator(data['Close']).rsi()
    fig.add_trace(go.Scatter(x=data.index, y=rsi, name='RSI', line=dict(color='rosybrown')))
    # 70と30の水平線を追加 
    fig.add_shape(type='line', x0=data.index[0], x1=data.index[-1], y0=70, y1=70, line=dict(color='palevioletred', width=2, dash='dash')) 
    fig.add_shape(type='line', x0=data.index[0], x1=data.index[-1], y0=30, y1=30, line=dict(color='palevioletred', width=2, dash='dash'))

    fig.update_layout(title={'text': 'RSI：Relative Strength Index（相対力指数）', 'x': 0.5, 'y': 0.8, 'xanchor': 'center', 'yanchor': 'top'}, xaxis_rangeslider_visible=False, showlegend=False)
    return fig


# 直近RSIを計算する関数
def calculate_rsi(ticker, period, interval):
    data = get_stock_price(ticker, period = period, interval = interval)
    rsi = RSIIndicator(data['Close']).rsi()
    latest_rsi = rsi.iloc[-1]
    return latest_rsi

###############################################################################################################################################


# アプリ画面構成 #######################################################################
# StreamlitでPlotlyグラフを表示
st.plotly_chart(plot_stock_price(ticker, period, interval, '日経平均株価'))
st.divider()

# RSIグラフを表示
st.plotly_chart(plot_stock_rsi(ticker, period, interval))
st.metric('現在のRSI', "{:,.1f}".format(calculate_rsi(ticker, period, interval)))
st.divider()

# 外部サイトリンクの埋め込み
st.header("外部サイトリンク")
st.link_button("騰落レシオ＆投資主体別履歴", "https://nikkei225jp.com/data/touraku.php")
#######################################################################################