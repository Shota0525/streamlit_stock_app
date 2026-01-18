import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta
from ta.volatility import BollingerBands
from datetime import datetime

# --- 設定 ---
period_map = {"6ヶ月": "6mo", "1年": "1y", "2年": "2y"}
interval = '1d'

# --- 関数定義 ---

def get_stock_price(ticker, period, interval, start=None, end=None):
    """株価データを取得する関数（最新yfinance対応版）"""
    try:
        # period指定か日付指定かで分岐
        if period:
            data = yf.download(ticker, period=period, interval=interval, progress=False)
        else:
            data = yf.download(ticker, start=start, end=end, interval=interval, progress=False)
        
        if data.empty:
            return pd.DataFrame()

        # 最新yfinanceのMultiIndex（2重列名）対策
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        # カラム名の整理（Adj Closeがない場合の補填）
        if 'Adj Close' not in data.columns:
            data['Adj Close'] = data['Close']
            
        return data
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        return pd.DataFrame()

def plot_stock_price(ticker, period, interval, title, buy_dates, sell_dates, start_date=None, end_date=None):
    """株価チャートを描画する関数"""
    data = get_stock_price(ticker, period, interval, start=start_date, end=end_date)
    
    if data.empty:
        st.warning("表示するデータがありません。")
        return go.Figure()

    fig = go.Figure()
    
    # 株価本体と移動平均線
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='株価', line=dict(color='gray', width=2)))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=25).mean(), name='MA25', line=dict(color='lightcoral')))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=50).mean(), name='MA50', line=dict(color='lightblue')))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'].rolling(window=75).mean(), name='MA75', line=dict(color='lightsalmon')))

    # ボリンジャーバンド
    indicator_bb = BollingerBands(close=data["Close"], window=20, window_dev=2)
    fig.add_trace(go.Scatter(x=data.index, y=indicator_bb.bollinger_hband(), name='BB+2σ', line=dict(color='#BDBDBD', dash='dash')))
    fig.add_trace(go.Scatter(x=data.index, y=indicator_bb.bollinger_lband(), name='BB-2σ', line=dict(color='#BDBDBD', dash='dash')))

    # タイムゾーン考慮のため日付を文字列にして比較
    data_idx_str = data.index.strftime('%Y-%m-%d')
    buy_str = [pd.to_datetime(d).strftime('%Y-%m-%d') for d in buy_dates]
    sell_str = [pd.to_datetime(d).strftime('%Y-%m-%d') for d in sell_dates]

    # 売買ポイントの描画
    buy_points = data[data_idx_str.isin(buy_str)]
    fig.add_trace(go.Scatter(x=buy_points.index, y=buy_points['Close'], name='買付', mode='markers', marker=dict(color='forestgreen', size=12, symbol='triangle-up')))

    sell_points = data[data_idx_str.isin(sell_str)]
    fig.add_trace(go.Scatter(x=sell_points.index, y=sell_points['Close'], name='売付', mode='markers', marker=dict(color='crimson', size=12, symbol='triangle-down')))

    fig.update_layout(title={'text': title, 'x': 0.5}, xaxis_rangeslider_visible=False, height=600)
    return fig

# --- メイン処理 ---

# データの読み込み
input_data = 'data/'
try:
    rakuten_nisa = pd.read_excel(input_data + '02_運用_rakuten.xlsx', sheet_name='国内株式_NISA')
    rakuten_tokutei = pd.read_excel(input_data + '02_運用_rakuten.xlsx', sheet_name='国内株式_特定')
    rakuten = pd.concat([rakuten_nisa, rakuten_tokutei])
    rakuten['銘柄コード'] = rakuten['銘柄コード'].astype(str)
except Exception as e:
    st.error(f"Excelファイルの読み込みに失敗しました: {e}")
    st.stop()

# 銘柄リスト作成
stock_info = rakuten[['銘柄コード', '銘柄名']].drop_duplicates()
stock_name_list = [f"{code}：{name}" for code, name in zip(stock_info['銘柄コード'], stock_info['銘柄名'])]
stock_name_list.sort()

# UI設定
selected_stock = st.selectbox('売買銘柄', stock_name_list)

# 選択情報の抽出
stock_code = selected_stock.split('：')[0]
stock_name = selected_stock.split('：')[1]
ticker = stock_code + '.T'

st.divider()

# --- 期間設定UIの追加 ---
col1, col2 = st.columns(2)

with col1:
    period_choice = st.selectbox(
        "表示期間設定",
        options=["6ヶ月", "1年", "2年", "日付指定"],
        index=1
    )

selected_period = None
start_dt = None
end_dt = None

if period_choice == "日付指定":
    with col2:
        start_dt = st.date_input("開始日", datetime(2023, 1, 1))
        end_dt = st.date_input("終了日", datetime.now())
else:
    selected_period = period_map[period_choice]

# 取引データの取得
target_data = rakuten[rakuten['銘柄コード'] == stock_code]
buy_dates = list(target_data[target_data['売買区分'] == '買付']['約定日'])
sell_dates = list(target_data[target_data['売買区分'] == '売付']['約定日'])

# グラフ表示
st.plotly_chart(plot_stock_price(ticker, selected_period, interval, stock_name, buy_dates, sell_dates, start_dt, end_dt), use_container_width=True)

# 取引履歴テーブル
st.subheader('取引履歴詳細')
history = target_data[['約定日', '口座区分', '売買区分', '単価［円］', '実現損益[円]']].copy()
history['約定日'] = pd.to_datetime(history['約定日']).dt.strftime('%Y-%m-%d')
st.dataframe(history.sort_values('約定日', ascending=False), use_container_width=True, hide_index=True)

# サマリー表示
total_pnl = target_data['実現損益[円]'].sum()
m1, m2, m3 = st.columns(3)
m1.metric("総取引数", len(history))
m2.metric("買付数", len(buy_dates))
m3.metric("累計実現損益", f"{total_pnl:,.0f} 円")