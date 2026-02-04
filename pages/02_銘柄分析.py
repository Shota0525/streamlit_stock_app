# ライブラリをインポート
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

# 基本条件を指定
interval = '1d'

# 各関数を定義 #################################################################################################################################
# 株価を取得する関数
def get_stock_price(ticker, period, interval):
    """最新yfinance対応版: MultiIndex解除と列名の整理"""
    data = yf.download(ticker, period=period, interval=interval, progress=False)
    
    if data.empty:
        return pd.DataFrame()
    
    # 1. 最新yfinanceのMultiIndex対策
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    return data

# 株関連データから必要な情報を取得する関数
def get_stock_data(stock_data, infoname):
    return stock_data.info.get(infoname, None)

# 株価データを描画する関数
def plot_stock_price(data, title):
    fig = make_subplots(rows=1, cols=1, shared_xaxes=True, vertical_spacing=0.03)

    # 色の視認性を改善
    fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name='original', increasing_line_color='#00FF00', decreasing_line_color='#FF0000'))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=5).mean(), name='MA5', line=dict(color='#F99C30')))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=25).mean(), name='MA25', line=dict(color='#52B8FF')))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=50).mean(), name='MA50', line=dict(color='#E17EC0')))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=75).mean(), name='MA75', line=dict(color='#3E77C4')))
    # ボリンジャーバンドも描画
    indicator_bb = BollingerBands(close=data["Close"], window=20, window_dev=2)
    fig.add_trace(go.Scatter(x=data.index, y=indicator_bb.bollinger_hband(), name='BB+2σ', line=dict(color='#BDBDBD', dash='dash')))
    fig.add_trace(go.Scatter(x=data.index, y=indicator_bb.bollinger_lband(), name='BB-2σ', line=dict(color='#BDBDBD', dash='dash')))

    fig.update_layout(title={'text': title, 'x': 0.5, 'y': 0.9, 'xanchor': 'center', 'yanchor': 'top'}, xaxis_rangeslider_visible=False, height=600)
    return fig

# 25日移動平均線と乖離率を計算する関数
def calculate_ma_deviation(data):
    ma25 = data['Close'].rolling(window=25).mean()
    deviation = (data['Close'] - ma25) / ma25 * 100
    return deviation.iloc[-1]

# 平均足を計算する関数
def plot_heikin_ashi(data):
    ha_df = data.copy()
    ha_df['HA_Close'] = (data['Open'] + data['High'] + data['Low'] + data['Close']) / 4
    
    # Openの計算（1つ前の要素に依存するためループ、または漸化式的処理が必要ですが近似で対応）
    ha_open = np.zeros(len(data))
    ha_open[0] = (data['Open'].iloc[0] + data['Close'].iloc[0]) / 2
    for i in range(1, len(data)):
        ha_open[i] = (ha_open[i-1] + ha_df['HA_Close'].iloc[i-1]) / 2
    ha_df['HA_Open'] = ha_open
    
    ha_df['HA_High'] = ha_df[['High', 'HA_Open', 'HA_Close']].max(axis=1)
    ha_df['HA_Low'] = ha_df[['Low', 'HA_Open', 'HA_Close']].min(axis=1)
    
    #fig = make_subplots(rows=1, cols=1)
    #fig.add_trace(go.Candlestick(x=ha_df.index, open=ha_df['HA_Open'], high=ha_df['HA_High'], low=ha_df['HA_Low'], close=ha_df['HA_Close'], name='平均足', increasing_line_color='tomato', decreasing_line_color='cornflowerblue'))
    # 平均足を描画
    fig = make_subplots(rows=1, cols=1, shared_xaxes=True, vertical_spacing=0.03)
    fig.add_trace(go.Candlestick(x=data.index, open=ha_df['HA_Open'], high=ha_df['HA_High'], low=ha_df['HA_Low'], close=ha_df['HA_Close'], name='original', increasing_line_color='#00FF00', decreasing_line_color='#FF0000'))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=50).mean(), name='MA50', line=dict(color='#E17EC0')))

    # ボリンジャーバンドも描画
    indicator_bb = BollingerBands(close=data["Close"], window=20, window_dev=2)
    fig.add_trace(go.Scatter(x=data.index, y=indicator_bb.bollinger_hband(), name='Upper BB', line=dict(color='palevioletred', dash='dash')))
    fig.add_trace(go.Scatter(x=data.index, y=indicator_bb.bollinger_lband(), name='Lower BB', line=dict(color='palevioletred', dash='dash')))

    fig.update_layout(title={'text': '平均足', 'x': 0.5}, xaxis_rangeslider_visible=False, height=500)
    return fig

# 一目均衡表を作成する関数
def plot_ichimoku(data):  
    # 転換線・基準線の計算
    max26 = data['High'].rolling(window=26).max()
    min26 = data['Low'].rolling(window=26).min()
    data['basic_line'] = (max26 + min26) / 2
    
    max9 = data['High'].rolling(window=9).max()
    min9 = data['Low'].rolling(window=9).min()
    data['turn_line'] = (max9 + min9) / 2
    
    # 先行スパンの計算
    data['span1'] = (data['basic_line'] + data['turn_line']) / 2
    
    high_52 = data['High'].rolling(window=52).max()
    low_52 = data['Low'].rolling(window=52).min()
    data['span2'] = ((high_52 + low_52) / 2)
    
    # 遅行線の計算
    data['slow_line'] = data['Close'].shift(-25)
    
    # プロットの区切りを設定 
    fig = make_subplots(rows=1, cols=1, shared_xaxes=True, vertical_spacing=0.03) 
    
    # 株価データを描画 
    fig.add_trace(go.Candlestick(
        x=data.index, 
        open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], 
        name='株価', # 凡例名をわかりやすく変更
        increasing_line_color='#00FF00', 
        decreasing_line_color='#FF0000'
    ))
    
    # 一目均衡表を追加描画 
    fig.add_trace(go.Scatter(x=data.index, y=data['turn_line'], name='転換線', line=dict(color='lightsalmon'))) 
    fig.add_trace(go.Scatter(x=data.index, y=data['basic_line'], name='基準線', line=dict(color='lightblue'))) 
    fig.add_trace(go.Scatter(x=data.index, y=data['slow_line'], name='遅行線', line=dict(color='lightgreen')))

    # SpanAとSpanBの間をグレーで塗りつぶす 
    fig.add_trace(go.Scatter(
        x=data.index, y=data['span1'], 
        line=dict(color='rgba(128, 128, 128, 0.5)', width=0), 
        fill=None, 
        showlegend=False # 塗りつぶしの片方は凡例非表示
    )) 
    fig.add_trace(go.Scatter(
        x=data.index, y=data['span2'], 
        line=dict(color='rgba(128, 128, 128, 0.5)', width=0), 
        fill='tonexty', 
        fillcolor='rgba(128, 128, 128, 0.5)', 
        name='雲（抵抗帯）' # 凡例に表示
    ))
    
    # レイアウト設定：凡例をグラフ上部に水平に配置
    fig.update_layout(
        title={'text': '一目均衡表', 'x': 0.5, 'y': 0.95, 'xanchor': 'center', 'yanchor': 'top'}, 
        xaxis_rangeslider_visible=False, 
        showlegend=True, # 凡例を表示
        legend=dict(
            orientation="h",       # 水平(horizontal)に並べる
            yanchor="bottom",      # 凡例の下側を基準にする
            y=1.02,                # グラフのすぐ上(1.0以上)に配置
            xanchor="center",      # 凡例の中央を基準にする
            x=0.5                  # グラフの中央に配置
        ),
        margin=dict(t=100)         # 凡例とタイトルが重ならないよう上部マージンを確保
    )
    return fig

# RSIを描画する関数
def plot_stock_rsi(data):
    rsi = RSIIndicator(data['Close']).rsi()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=rsi, name='RSI', line=dict(color='rosybrown')))
    fig.add_hline(y=70, line_dash="dash", line_color="red")
    fig.add_hline(y=30, line_dash="dash", line_color="green")
    fig.update_layout(title={'text': 'RSI：Relative Strength Index（相対力指数）', 'x': 0.5, 'xanchor': 'center'}, yaxis=dict(range=[0, 100]), height=300)
    return fig

# MACDをプロットする関数
def plot_macd_histogram(data):
    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    
    fig = make_subplots(rows=1, cols=1)
    fig.add_trace(go.Bar(x=data.index, y=hist, name='ヒストグラム', marker_color='gray'))
    fig.add_trace(go.Scatter(x=data.index, y=macd, name='MACD', line=dict(color='#00E5FF')))
    fig.add_trace(go.Scatter(x=data.index, y=signal, name='Signal', line=dict(color='tomato')))
    fig.update_layout(title={'text': 'MACD', 'x': 0.5}, height=300)
    return fig

# 出来高を表示する関数
def plot_volume(data):
    colors = ['#00FF00' if c >= o else '#FF0000' for c, o in zip(data['Close'], data['Open'])]
    fig = go.Figure(go.Bar(x=data.index, y=data['Volume'], marker_color=colors, name='出来高'))
    fig.update_layout(title={'text':'出来高', 'x': 0.5}, height=250)
    return fig

# --- メイン処理 ---
input_data = 'data/'
try:
    jpx = pd.read_excel(input_data + 'JPX_業種区分マスタ.xlsx')
    jpx['コード'] = jpx['コード'].astype(str)
except:
    st.error("JPXマスタの読み込みに失敗しました。")
    st.stop()

stock_info = jpx[['コード', '銘柄名']].drop_duplicates()
stock_name_list = [f"{code}：{name}" for code, name in zip(stock_info['コード'], stock_info['銘柄名'])]
stock_name_list.sort()

selected_stock = st.selectbox('分析銘柄', stock_name_list)
stock_code = selected_stock.split('：')[0]
ticker = stock_code + '.T'
stock_name = selected_stock.split('：')[1]

period = st.selectbox('表示期間', ['6mo', '1y', '2y'], index=0)
data = get_stock_price(ticker, period, interval)

if not data.empty:
    st.plotly_chart(plot_stock_price(data, stock_name), use_container_width=True)
    
    c1, c2 = st.columns(2)
    c1.metric('25日乖離率', f"{calculate_ma_deviation(data):.1f}%")
    c2.caption("買い目安: -15%以下 / 売り目安: +15%以上")
    
    st.plotly_chart(plot_heikin_ashi(data), use_container_width=True)
    st.plotly_chart(plot_volume(data), use_container_width=True)
    st.plotly_chart(plot_ichimoku(data), use_container_width=True)
    st.plotly_chart(plot_stock_rsi(data), use_container_width=True)
    st.plotly_chart(plot_macd_histogram(data), use_container_width=True)

    # 企業詳細情報の取得
    stock_obj = yf.Ticker(ticker)
    info = stock_obj.info
    
    st.subheader("📋 銘柄詳細データ")
    m1, m2, m3 = st.columns(3)
    m1.metric("最新株価", f"{info.get('currentPrice', 0):,} 円")
    m2.metric("配当利回り", f"{info.get('dividendYield', 0)*100:.2f} %")
    m3.metric("PER", f"{info.get('trailingPE', 0):.2f}")