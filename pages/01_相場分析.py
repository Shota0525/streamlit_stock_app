# ライブラリをインポート
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ta.momentum import RSIIndicator
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
def plot_stock_price(ticker, period, interval, title):
    data = get_stock_price(ticker, period=period, interval=interval)
    if data.empty:
        return go.Figure()

    # プロットの区切りを設定
    fig = make_subplots(rows=1, cols=1, shared_xaxes=True, vertical_spacing=0.03)

    # 株価データと移動曲線を描画
    fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], 
                                 name='original', increasing_line_color='#00FF00', decreasing_line_color='#FF0000'))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=5).mean(), name='MA5', line=dict(color='#F99C30')))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=25).mean(), name='MA25', line=dict(color='#52B8FF')))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=50).mean(), name='MA50', line=dict(color='#E17EC0')))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=75).mean(), name='MA75', line=dict(color='#3E77C4')))

    # ボリンジャーバンド
    indicator_bb = BollingerBands(close=data["Close"], window=20, window_dev=2)
    fig.add_trace(go.Scatter(x=data.index, y=indicator_bb.bollinger_hband(), name='Upper BB', line=dict(color='palevioletred', dash='dash')))
    fig.add_trace(go.Scatter(x=data.index, y=indicator_bb.bollinger_lband(), name='Lower BB', line=dict(color='palevioletred', dash='dash')))

    # 凡例を上部に配置
    fig.update_layout(
        title={'text': title, 'x': 0.5, 'y': 0.95, 'xanchor': 'center', 'yanchor': 'top'},
        xaxis_rangeslider_visible=False,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(t=100)
    )
    return fig

# RSIを描画する関数
def plot_stock_rsi(ticker, period, interval):
    data = get_stock_price(ticker, period=period, interval=interval)
    if data.empty:
        return go.Figure()

    fig = make_subplots(rows=1, cols=1, shared_xaxes=True, vertical_spacing=0.03)
    rsi = RSIIndicator(data['Close']).rsi()
    
    # RSIを描画（色は元のまま維持）
    fig.add_trace(go.Scatter(x=data.index, y=rsi, name='RSI', line=dict(color='rosybrown')))
    
    # 水平線（色は元のまま維持）
    fig.add_hline(y=70, line_dash="dash", line_color="red") 
    fig.add_hline(y=30, line_dash="dash", line_color="green")

    fig.update_layout(
        title={'text': 'RSI：Relative Strength Index（相対力指数）', 'x': 0.5, 'y': 0.95, 'xanchor': 'center', 'yanchor': 'top'},
        xaxis_rangeslider_visible=False,
        margin=dict(t=100),
        yaxis=dict(range=[0, 100])
    )
    return fig

# 直近RSIを計算する関数
def calculate_rsi(ticker, period, interval):
    data = get_stock_price(ticker, period=period, interval=interval)
    if data.empty: return 0
    rsi = RSIIndicator(data['Close']).rsi()
    return rsi.iloc[-1]

###############################################################################################################################################

# アプリ画面構成 #######################################################################
# 銘柄と期間の選択
col_set1, col_set2 = st.columns(2)
with col_set1:
    # 銘柄入力を反映
    ticker_input = st.text_input('ティッカーシンボル', '^N225')
with col_set2:
    # 6moをデフォルトに設定 (index=0)
    period = st.selectbox('表示期間', ['6mo', '1y', '2y'], index=0)

interval = '1d'

# 各グラフを表示
st.plotly_chart(plot_stock_price(ticker_input, period, interval, '日経平均株価'))
st.divider()

st.plotly_chart(plot_stock_rsi(ticker_input, period, interval))
st.metric('現在のRSI', "{:,.1f}".format(calculate_rsi(ticker_input, period, interval)))
st.divider()

# 外部サイトリンク
st.header("外部サイトリンク")
st.link_button("騰落レシオ＆投資主体別履歴", "https://nikkei225jp.com/data/touraku.php")
st.link_button("日経平均 ヒートマップ", "https://nikkei225jp.com/nikkei/")
st.link_button("決算速報（株探）", "https://kabutan.jp/news/")
#######################################################################################