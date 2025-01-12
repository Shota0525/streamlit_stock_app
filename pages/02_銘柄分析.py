# ライブラリをインポート
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands


# 基本条件を指定
################
interval = '1d'
################

# 各関数を定義 #################################################################################################################################
# 株価を取得する関数
def get_stock_price(ticker, period, interval):
    data = yf.download(ticker, period = period, interval = interval)
    return data

# 株関連データから必要な情報を取得する関数
def get_stock_data(stock_data, infoname):
    info_data = stock_data.info.get(infoname, None)
    return info_data


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


# 25日移動平均線と乖離率を計算する関数
def calculate_ma_deviation(ticker, period, interval):
    data = get_stock_price(ticker, period = period, interval = interval)
    data['MA25'] = data['Close'].rolling(window=25).mean() # 25日移動平均線 
    data['Deviation'] = (data['Close'] - data['MA25']) / data['MA25'] * 100 # 乖離率 
    latest_deviation = data['Deviation'].iloc[-1]
    return latest_deviation


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


# MACDとシグナル線を計算し、ヒストグラムをプロットする関数
def plot_macd_histogram(ticker, period, interval):
    data = get_stock_price(ticker, period, interval)
    
    # MACDを計算
    short_window = 12
    long_window = 26
    signal_window = 9
    
    data['EMA12'] = data['Close'].ewm(span=short_window, adjust=False).mean()
    data['EMA26'] = data['Close'].ewm(span=long_window, adjust=False).mean()
    data['MACD'] = data['EMA12'] - data['EMA26']
    data['Signal'] = data['MACD'].ewm(span=signal_window, adjust=False).mean()
    data['Histogram'] = data['MACD'] - data['Signal']
    
    # プロットの区切りを設定
    fig = go.Figure()
    # MACDのヒストグラムを棒グラフで描画
    fig.add_trace(go.Bar(x=data.index, y=data['Histogram'], name='MACD Histogram', marker_color='lightgray'))
    # MACDのラインを折れ線グラフで描画
    fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], mode='lines', name='MACD', line=dict(color='lightblue')))
    # シグナル線を折れ線グラフで描画
    fig.add_trace(go.Scatter(x=data.index, y=data['Signal'], mode='lines', name='Signal Line', line=dict(color='lightcoral')))
    # グラフのタイトルとレイアウトを設定
    fig.update_layout(title={'text': '【MACD】Blue,  【Signal】Red', 'x': 0.5, 'y': 0.8, 'xanchor': 'center', 'yanchor': 'top'}, xaxis_rangeslider_visible=False, showlegend=False)
    return fig
###############################################################################################################################################


# データ取得 ###########################################################################
# ディレクトリを指定
input_data = 'data/'

# データの読み込み
jpx = pd.read_excel(input_data + 'JPX_業種区分マスタ.xlsx')
jpx['コード'] = jpx['コード'].astype(str)  # 銘柄コード列を文字列に変換

# 売買したことのある銘柄の名前を取得しリスト化
stock_info = jpx[['コード', '銘柄名']].drop_duplicates()
stock_name_list = [f"{code}：{name}" for code, name in zip(stock_info['コード'], stock_info['銘柄名'])]
stock_name_list.sort()
#######################################################################################


# アプリ画面構成 #######################################################################
# selectboxの設定
selected_stock = st.selectbox('分析銘柄', stock_name_list)

# 選択された文字列から銘柄コードと銘柄名を取得
stock_code = selected_stock.split('：')[0]
ticker = stock_code + '.T'
stock_name = selected_stock.split('：')[1]

# 表示期間の指定
period_list = ['6mo', '1y', '2y']
period = st.selectbox('表示期間', period_list)
st.divider()  # 水平線を追加

    
# 株価データグラフを表示
st.plotly_chart(plot_stock_price(ticker, period, interval, stock_name))
col1, col2 = st.columns(2)
with col1:
    st.metric('25日移動平均線乖離率（％）', "{:,.1f}".format(calculate_ma_deviation(ticker, period, interval)))
with col2:
    st.caption("""
    買いシグナル：-15 ~ -20％以下\n
    売りシグナル：+15 ~ +20％以上
    """)

# RSIグラフを表示
st.plotly_chart(plot_stock_rsi(ticker, period, interval))
st.metric('現在のRSI', "{:,.1f}".format(calculate_rsi(ticker, period, interval)))

# MACDグラフを表示
st.plotly_chart( plot_macd_histogram(ticker, period, interval))


# yfinanceから株関連データを取得
stock_data = yf.Ticker(ticker)
current_Price = get_stock_data(stock_data, 'currentPrice')  # 最新株価
market_cap = get_stock_data(stock_data, 'marketCap')  # 時価総額
dividend_Rate = get_stock_data(stock_data, 'dividendRate')  # 年間配当金
dividend_yield = get_stock_data(stock_data, 'dividendYield')  # 配当利回り
payout_Ratio = get_stock_data(stock_data, 'payoutRatio')  # 配当性向
pbr = get_stock_data(stock_data, 'priceToBook')  # PBR
per = get_stock_data(stock_data, 'trailingPE')  # PER（直近12ヶ月の利益に基づく）
return_OnEquity = get_stock_data(stock_data, 'returnOnEquity')  #  ROE（自己資本利益率）
total_Revenue = get_stock_data(stock_data, 'totalRevenue')  # 総売上高
operating_Margins = get_stock_data(stock_data, 'operatingMargins')  # 営業利益率
target_Mean_Price = get_stock_data(stock_data, 'targetMeanPrice')  # 目標株価（アナリスト平均）
    
# 詳細情報を表示
col1, col2 = st.columns(2)
with col1:
    if market_cap is not None:
        st.metric('時価総額（億円）', "{:,.2f}".format(market_cap/10**8))
    if current_Price is not None:
        st.metric('最新株価（円）', "{:,.1f}".format(current_Price))
    if target_Mean_Price is not None:
        st.metric('目標株価（アナリスト平均）', "{:,.2f}".format(target_Mean_Price))
    if dividend_Rate is not None:
        st.metric('年間配当金（円）', "{:,.2f}".format(dividend_Rate))
    if dividend_yield is not None:
        st.metric('配当利回り（％）', "{:,.2f}".format(dividend_yield*100))
    if payout_Ratio is not None:
        st.metric('配当性向（％）', "{:,.2f}".format(payout_Ratio*100))    
with col2:
    if pbr is not None:
        st.metric('PBR（株価純資産倍率; 東証平均1.5倍）', "{:,.2f}".format(pbr))
    if per is not None:
        st.metric('PER（株価収益率; 東証平均15倍）', "{:,.2f}".format(per))
    if return_OnEquity is not None:
        st.metric('ROE（自己資本利益率≒経営効率; 目安8％）', "{:,.2f}".format(return_OnEquity*100))    
    if total_Revenue is not None:
        st.metric('総売上高（億円）', "{:,.2f}".format(total_Revenue/10**8))
    if operating_Margins is not None:
        st.metric('営業利益率（％）', "{:,.2f}".format(operating_Margins*100))
#######################################################################################

