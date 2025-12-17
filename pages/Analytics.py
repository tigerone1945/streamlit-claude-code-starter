import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Order Analytics", layout="wide")

st.title("Order Analytics")

@st.cache_data
def load_analysis_data():
    try:
        orders_df = pd.read_csv("sample_data/orders.csv")
        users_df = pd.read_csv("sample_data/users.csv")

        # 日付型への変換
        orders_df['created_at'] = pd.to_datetime(orders_df['created_at'])
        users_df['created_at'] = pd.to_datetime(users_df['created_at'])

        # ordersとusersを結合（国・トラフィックソース情報取得のため）
        merged_df = orders_df.merge(
            users_df[['id', 'country', 'traffic_source']],
            left_on='user_id',
            right_on='id',
            how='left',
            suffixes=('', '_user')
        )

        # 結合後の欠損値を削除
        merged_df = merged_df.dropna(subset=['country', 'traffic_source'])

        return merged_df
    except FileNotFoundError:
        st.error("データファイルが見つかりません。sample_data/ディレクトリを確認してください。")
        st.stop()
    except Exception as e:
        st.error(f"データ読み込みエラー: {str(e)}")
        st.stop()

def calculate_monthly_metrics(df):
    try:
        # データフレームのコピーを作成
        df = df.copy()
        # 年月カラム追加
        df['year_month'] = df['created_at'].dt.to_period('M')

        # 月別集計
        monthly_stats = df.groupby('year_month').agg({
            'order_id': 'count',
            'status': lambda x: (x == 'Cancelled').sum()
        }).reset_index()

        monthly_stats.columns = ['year_month', 'total_orders', 'cancelled_orders']
        monthly_stats['cancel_rate'] = (
            monthly_stats['cancelled_orders'] / monthly_stats['total_orders'] * 100
        )

        # Period型を文字列に変換（Plotly用）
        monthly_stats['year_month'] = monthly_stats['year_month'].astype(str)

        return monthly_stats
    except Exception as e:
        st.error(f"月次集計エラー: {str(e)}")
        st.stop()

# データ読み込み
merged_df = load_analysis_data()

# サイドバーフィルタ
st.sidebar.header("Filters")

# 国別フィルタ
all_countries = sorted(merged_df['country'].unique())
selected_countries = st.sidebar.multiselect(
    "Select Countries",
    options=all_countries,
    default=all_countries[:5] if len(all_countries) >= 5 else all_countries
)

# トラフィックソース別フィルタ
all_traffic_sources = sorted(merged_df['traffic_source'].unique())
selected_traffic_sources = st.sidebar.multiselect(
    "Select Traffic Sources",
    options=all_traffic_sources,
    default=all_traffic_sources
)

# フィルタ適用
filtered_df = merged_df[
    (merged_df['country'].isin(selected_countries)) &
    (merged_df['traffic_source'].isin(selected_traffic_sources))
]

# フィルタリング後の空データチェック
if filtered_df.empty:
    st.warning("選択された条件に該当するデータがありません。フィルタを調整してください。")
    st.stop()

# 月次集計実行
monthly_stats = calculate_monthly_metrics(filtered_df)

# メインエリア表示
st.subheader("Monthly Order Trends")

# 概要メトリクス表示
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Orders", f"{len(filtered_df):,}")
with col2:
    avg_cancel_rate = (filtered_df['status'] == 'Cancelled').sum() / len(filtered_df) * 100
    st.metric("Average Cancel Rate", f"{avg_cancel_rate:.2f}%")
with col3:
    st.metric("Months Analyzed", len(monthly_stats))

st.divider()

# 1. 月別オーダー数推移（棒グラフ）
st.subheader("Monthly Order Volume")
fig_orders = px.bar(
    monthly_stats,
    x='year_month',
    y='total_orders',
    title='Monthly Order Count Trend',
    labels={'year_month': 'Month', 'total_orders': 'Number of Orders'},
    color='total_orders',
    color_continuous_scale='Blues'
)
fig_orders.update_layout(
    height=450,
    showlegend=False,
    xaxis_tickangle=-45
)
st.plotly_chart(fig_orders, use_container_width=True)

# 2. 月別キャンセル率推移（折れ線グラフ）
st.subheader("Monthly Cancellation Rate")
fig_cancel = px.line(
    monthly_stats,
    x='year_month',
    y='cancel_rate',
    title='Monthly Cancellation Rate Trend',
    labels={'year_month': 'Month', 'cancel_rate': 'Cancellation Rate (%)'},
    markers=True
)
fig_cancel.update_layout(
    height=450,
    xaxis_tickangle=-45
)
fig_cancel.update_traces(line_color='#FF6B6B', marker=dict(size=8))
st.plotly_chart(fig_cancel, use_container_width=True)

# 3. 複合グラフ（2軸：注文数 + キャンセル率）
st.subheader("Combined View: Order Volume & Cancellation Rate")
fig_combined = go.Figure()

# 棒グラフ（注文数）
fig_combined.add_trace(go.Bar(
    x=monthly_stats['year_month'],
    y=monthly_stats['total_orders'],
    name='Order Count',
    marker_color='#4A90E2',
    yaxis='y'
))

# 折れ線グラフ（キャンセル率）
fig_combined.add_trace(go.Scatter(
    x=monthly_stats['year_month'],
    y=monthly_stats['cancel_rate'],
    name='Cancel Rate (%)',
    mode='lines+markers',
    marker=dict(size=8, color='#FF6B6B'),
    line=dict(width=3, color='#FF6B6B'),
    yaxis='y2'
))

# レイアウト設定
fig_combined.update_layout(
    title='Monthly Orders and Cancellation Rate',
    xaxis=dict(title='Month', tickangle=-45),
    yaxis=dict(
        title=dict(text='Number of Orders', font=dict(color='#4A90E2')),
        tickfont=dict(color='#4A90E2')
    ),
    yaxis2=dict(
        title=dict(text='Cancellation Rate (%)', font=dict(color='#FF6B6B')),
        tickfont=dict(color='#FF6B6B'),
        overlaying='y',
        side='right'
    ),
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=1.02,
        xanchor='right',
        x=1
    ),
    height=500,
    hovermode='x unified'
)

st.plotly_chart(fig_combined, use_container_width=True)

# 4. 月次データテーブル
st.subheader("Monthly Summary Data")
display_stats = monthly_stats.copy()
display_stats['cancel_rate'] = display_stats['cancel_rate'].round(2)
display_stats.columns = ['Month', 'Total Orders', 'Cancelled Orders', 'Cancel Rate (%)']

st.dataframe(
    display_stats,
    use_container_width=True,
    hide_index=True
)
