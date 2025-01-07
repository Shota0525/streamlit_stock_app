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
period = '2y'
interval = '1d'
################


# 各関数を定義 #################################################################################################################################
# 株価を取得する関数
def get_stock_price(ticker, period, interval):
    data = yf.download(ticker, period = period, interval = interval)
    return data


# 株価データを描画する関数
def plot_stock_price(ticker, period, interval, title, buy, sell):
    data = get_stock_price(ticker, period = period, interval = interval)
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
    
    # 買付日リストの点を赤色で追加
    buy_data = data[data.index.isin(buy)]
    fig.add_trace(go.Scatter(x=buy_data.index, y=buy_data['Close'], name='Buy Dates', mode='markers', marker=dict(color='forestgreen', size=10, symbol='circle')))

    # 売付日リストの点を青色で追加
    sell_data = data[data.index.isin(sell)]
    fig.add_trace(go.Scatter(x=sell_data.index, y=sell_data['Close'], name='Sell Dates', mode='markers', marker=dict(color='crimson', size=10, symbol='circle')))
    
    fig.update_layout(title={'text': title, 'x': 0.5, 'y': 0.8, 'xanchor': 'center', 'yanchor': 'top'}, xaxis_rangeslider_visible=False, showlegend=False)
    return fig


# 特定の銘柄コードの約定日と売買区分を取得する関数を定義
def get_transaction_details(df, stock_code):
    filtered_df = df[df['銘柄コード'] == stock_code]
    transaction = filtered_df[['銘柄コード','銘柄名','約定日', '売買区分', '単価［円］', '実現損益[円]']]
    return transaction

# 売買の日付をリストで取得
def get_trade_date_list(df, buy_or_sell):
    trade_date = df[df['売買区分'] == buy_or_sell]
    trade_date_list = list(trade_date['約定日'])
    return trade_date_list

# 売買損益を計算する関数を定義
def calculate_total_pnl(df, stock_code): 
    target_stock = df[df['銘柄コード'] == stock_code]
    total_pnl = target_stock['実現損益[円]'].sum() 
    return total_pnl
#################################################################################################################################


# データ取得 ###########################################################################
# ディレクトリを指定
input_data = 'data/'

# データの読み込み
rakuten = pd.read_excel(input_data + '02_運用_rakuten.xlsx', sheet_name = '国内株式_特定')
rakuten['銘柄コード'] = rakuten['銘柄コード'].astype(str)  # 銘柄コード列を文字列に変換

# 売買したことのある銘柄の名前を取得しリスト化
stock_info = rakuten[['銘柄コード', '銘柄名']].drop_duplicates()
stock_name_list = [f"{code}：{name}" for code, name in zip(stock_info['銘柄コード'], stock_info['銘柄名'])]
stock_name_list.sort()
#######################################################################################



# アプリ画面構成 #######################################################################
# selectboxの設定
selected_stock = st.selectbox('売買銘柄', stock_name_list)

# 選択された文字列から銘柄コードと銘柄名を取得
stock_code = selected_stock.split('：')[0]
stock_name = selected_stock.split('：')[1]
st.divider()  # 水平線を追加


# 選択した銘柄の各種情報を取得
stock_code, = rakuten.loc[rakuten['銘柄名'] == stock_name, '銘柄コード'].unique()
target_data = get_transaction_details(rakuten, stock_code)
buy = get_trade_date_list(target_data, '買付')
sell = get_trade_date_list(target_data, '売付')
ticker = stock_code + '.T'


# StreamlitでPlotlyグラフを表示
st.plotly_chart(plot_stock_price(ticker, period, interval, stock_name, buy, sell))


# 取引履歴の詳細を表示
st.subheader('取引履歴')

# 取引データを整形して表示
transaction_history = target_data[['約定日', '売買区分', '単価［円］', '実現損益[円]']]
# datetime型に変換してフォーマットを変更
transaction_history['約定日'] = pd.to_datetime(transaction_history['約定日'])  # datetime型に変換
transaction_history['約定日'] = transaction_history['約定日'].dt.strftime('%Y-%m-%d') 
transaction_history = transaction_history.sort_values('約定日')  # 日付でソート
st.dataframe(transaction_history, use_container_width=True, hide_index=True)  # 幅を画面に合わせる

# 基本情報を表示
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("総取引回数", len(transaction_history))
with col2:
    st.metric("買付回数", len(buy))
with col3:
    st.metric('売買損益', "{:,.0f}".format(calculate_total_pnl(rakuten, stock_code)))
##################################################################################################