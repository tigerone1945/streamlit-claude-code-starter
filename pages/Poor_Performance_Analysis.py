import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Poor Performance Analysis", layout="wide")

st.title("📉 Poor Performance Product Analysis")
st.markdown("**Phase 1**: Low Sales & Return Rate Analysis")

@st.cache_data
def load_data():
    """Load all necessary data"""
    order_items_df = pd.read_csv("sample_data/order_items.csv")
    products_df = pd.read_csv("sample_data/products.csv")
    orders_df = pd.read_csv("sample_data/orders.csv")

    # Convert date columns
    order_items_df['created_at'] = pd.to_datetime(order_items_df['created_at'])

    # Merge order items with products
    merged_df = order_items_df.merge(
        products_df,
        left_on='product_id',
        right_on='id',
        how='left',
        suffixes=('_order', '_product')
    )

    # Merge with orders to get gender info
    merged_df = merged_df.merge(
        orders_df[['order_id', 'gender']],
        on='order_id',
        how='left'
    )

    return merged_df, products_df, order_items_df

# Load data
merged_df, products_df, order_items_df = load_data()

# Sidebar filters
st.sidebar.header("Filters")

# Date range filter
st.sidebar.subheader("📅 Analysis Period")
min_date = merged_df['created_at'].min().date()
max_date = merged_df['created_at'].max().date()

period_type = st.sidebar.selectbox(
    "Select Period",
    ["All Time", "Last 30 Days", "Last 60 Days", "Last 90 Days"],
    index=0
)

if period_type == "All Time":
    filtered_df = merged_df.copy()
else:
    days = int(period_type.split()[1])
    cutoff_date = max_date - timedelta(days=days)
    filtered_df = merged_df[merged_df['created_at'].dt.date >= cutoff_date].copy()

st.sidebar.divider()

# Category filter
st.sidebar.subheader("🏷️ Category Filter")
all_categories = ['All'] + sorted(merged_df['category'].unique().tolist())
selected_category = st.sidebar.selectbox("Select Category", all_categories)

if selected_category != 'All':
    filtered_df = filtered_df[filtered_df['category'] == selected_category]

st.sidebar.divider()

# Department filter
st.sidebar.subheader("🏢 Department Filter")
selected_dept = st.sidebar.radio(
    "Select Department",
    ["All", "Men", "Women"],
    horizontal=True
)

if selected_dept != "All":
    filtered_df = filtered_df[filtered_df['department'] == selected_dept]

# Calculate product-level metrics
product_stats = filtered_df.groupby(['product_id', 'name', 'category', 'brand', 'department', 'cost', 'retail_price']).agg({
    'id_order': 'count',  # Total orders
    'sale_price': 'sum',   # Total revenue
    'status': lambda x: (x == 'Returned').sum()  # Return count
}).reset_index()

product_stats.columns = ['product_id', 'name', 'category', 'brand', 'department', 'cost', 'retail_price', 'total_sales_count', 'total_revenue', 'return_count']

# Calculate additional metrics
product_stats['return_rate'] = (product_stats['return_count'] / product_stats['total_sales_count'] * 100).round(2)
product_stats['avg_sale_price'] = (product_stats['total_revenue'] / product_stats['total_sales_count']).round(2)
product_stats['profit_per_item'] = (product_stats['avg_sale_price'] - product_stats['cost']).round(2)
product_stats['total_profit'] = (product_stats['profit_per_item'] * product_stats['total_sales_count']).round(2)
product_stats['profit_margin'] = ((product_stats['profit_per_item'] / product_stats['avg_sale_price']) * 100).round(2)

# Fill NaN values
product_stats = product_stats.fillna(0)

# Overview Section
st.header("📊 Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Products Analyzed",
        f"{len(product_stats):,}"
    )

with col2:
    avg_return_rate = (filtered_df['status'] == 'Returned').sum() / len(filtered_df) * 100
    st.metric(
        "Overall Return Rate",
        f"{avg_return_rate:.2f}%"
    )

with col3:
    low_sales_products = len(product_stats[product_stats['total_sales_count'] < 10])
    st.metric(
        "Low Sales Products",
        f"{low_sales_products:,}",
        help="Products with less than 10 sales"
    )

with col4:
    high_return_products = len(product_stats[product_stats['return_rate'] >= 15])
    st.metric(
        "High Return Products",
        f"{high_return_products:,}",
        help="Products with 15%+ return rate"
    )

st.divider()

# Tabs for different analyses
tab1, tab2, tab3 = st.tabs(["📉 Low Sales Analysis", "🔄 Return Rate Analysis", "💰 Profit Analysis"])

with tab1:
    st.header("Low Sales Product Dashboard")
    st.markdown("Identify products with poor sales performance")

    # Filter options
    col1, col2 = st.columns(2)

    with col1:
        sales_threshold = st.slider(
            "Sales Count Threshold (show products below this number)",
            min_value=1,
            max_value=50,
            value=10,
            step=1
        )

    with col2:
        sort_by = st.selectbox(
            "Sort By",
            ["Lowest Sales Count", "Highest Return Rate", "Lowest Profit", "Lowest Revenue"]
        )

    # Filter low sales products
    low_sales_df = product_stats[product_stats['total_sales_count'] <= sales_threshold].copy()

    # Sort based on selection
    if sort_by == "Lowest Sales Count":
        low_sales_df = low_sales_df.sort_values('total_sales_count', ascending=True)
    elif sort_by == "Highest Return Rate":
        low_sales_df = low_sales_df.sort_values('return_rate', ascending=False)
    elif sort_by == "Lowest Profit":
        low_sales_df = low_sales_df.sort_values('total_profit', ascending=True)
    else:  # Lowest Revenue
        low_sales_df = low_sales_df.sort_values('total_revenue', ascending=True)

    st.info(f"Found **{len(low_sales_df):,}** products with {sales_threshold} or fewer sales")

    # Display table
    st.subheader(f"Top 100 Poor Performance Products")

    display_df = low_sales_df.head(100)[['name', 'category', 'brand', 'department', 'total_sales_count', 'return_count', 'return_rate', 'total_revenue', 'total_profit', 'profit_margin']]

    st.dataframe(
        display_df.style.format({
            'total_sales_count': '{:,.0f}',
            'return_count': '{:,.0f}',
            'return_rate': '{:.2f}%',
            'total_revenue': '${:,.2f}',
            'total_profit': '${:,.2f}',
            'profit_margin': '{:.2f}%'
        }),
        use_container_width=True,
        height=400
    )

    # Visualizations
    st.subheader("Low Sales Visualizations")

    col1, col2 = st.columns(2)

    with col1:
        # Category breakdown
        category_low_sales = low_sales_df.groupby('category').size().reset_index(name='count').sort_values('count', ascending=False).head(10)

        fig_cat = px.bar(
            category_low_sales,
            x='count',
            y='category',
            orientation='h',
            title='Top 10 Categories with Most Low-Sales Products',
            labels={'count': 'Number of Products', 'category': 'Category'},
            color='count',
            color_continuous_scale='Reds'
        )
        fig_cat.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_cat, use_container_width=True)

    with col2:
        # Brand breakdown
        brand_low_sales = low_sales_df.groupby('brand').size().reset_index(name='count').sort_values('count', ascending=False).head(10)

        fig_brand = px.bar(
            brand_low_sales,
            x='count',
            y='brand',
            orientation='h',
            title='Top 10 Brands with Most Low-Sales Products',
            labels={'count': 'Number of Products', 'brand': 'Brand'},
            color='count',
            color_continuous_scale='Oranges'
        )
        fig_brand.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_brand, use_container_width=True)

    # Sales distribution
    st.subheader("Sales Distribution")

    fig_dist = px.histogram(
        low_sales_df,
        x='total_sales_count',
        nbins=20,
        title=f'Distribution of Sales Count (Products with ≤{sales_threshold} sales)',
        labels={'total_sales_count': 'Sales Count', 'count': 'Number of Products'},
        color_discrete_sequence=['#FF6B6B']
    )
    st.plotly_chart(fig_dist, use_container_width=True)

with tab2:
    st.header("Return Rate Analysis")
    st.markdown("Identify products with quality or satisfaction issues")

    # Filter options
    col1, col2 = st.columns(2)

    with col1:
        min_sales_for_return = st.slider(
            "Minimum Sales (to avoid statistical noise)",
            min_value=1,
            max_value=20,
            value=5,
            step=1,
            help="Only analyze products with at least this many sales"
        )

    with col2:
        return_threshold = st.slider(
            "Return Rate Threshold (%)",
            min_value=5,
            max_value=50,
            value=15,
            step=5
        )

    # Filter products with sufficient sales and high return rate
    high_return_df = product_stats[
        (product_stats['total_sales_count'] >= min_sales_for_return) &
        (product_stats['return_rate'] >= return_threshold)
    ].copy()

    high_return_df = high_return_df.sort_values('return_rate', ascending=False)

    st.info(f"Found **{len(high_return_df):,}** products with ≥{min_sales_for_return} sales and ≥{return_threshold}% return rate")

    # Display table
    st.subheader("High Return Rate Products (Top 100)")

    display_df = high_return_df.head(100)[['name', 'category', 'brand', 'department', 'total_sales_count', 'return_count', 'return_rate', 'total_revenue', 'avg_sale_price']]

    st.dataframe(
        display_df.style.format({
            'total_sales_count': '{:,.0f}',
            'return_count': '{:,.0f}',
            'return_rate': '{:.2f}%',
            'total_revenue': '${:,.2f}',
            'avg_sale_price': '${:.2f}'
        }),
        use_container_width=True,
        height=400
    )

    # Visualizations
    st.subheader("Return Rate Visualizations")

    col1, col2 = st.columns(2)

    with col1:
        # Category return rate
        category_returns = product_stats.groupby('category').agg({
            'return_count': 'sum',
            'total_sales_count': 'sum'
        }).reset_index()
        category_returns['return_rate'] = (category_returns['return_count'] / category_returns['total_sales_count'] * 100).round(2)
        category_returns = category_returns.sort_values('return_rate', ascending=False).head(10)

        fig_cat_return = px.bar(
            category_returns,
            x='return_rate',
            y='category',
            orientation='h',
            title='Top 10 Categories by Return Rate',
            labels={'return_rate': 'Return Rate (%)', 'category': 'Category'},
            color='return_rate',
            color_continuous_scale='Reds'
        )
        fig_cat_return.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_cat_return, use_container_width=True)

    with col2:
        # Brand return rate
        brand_returns = product_stats.groupby('brand').agg({
            'return_count': 'sum',
            'total_sales_count': 'sum'
        }).reset_index()
        brand_returns['return_rate'] = (brand_returns['return_count'] / brand_returns['total_sales_count'] * 100).round(2)
        brand_returns = brand_returns[brand_returns['total_sales_count'] >= 20]  # Filter brands with enough sales
        brand_returns = brand_returns.sort_values('return_rate', ascending=False).head(10)

        fig_brand_return = px.bar(
            brand_returns,
            x='return_rate',
            y='brand',
            orientation='h',
            title='Top 10 Brands by Return Rate (min 20 sales)',
            labels={'return_rate': 'Return Rate (%)', 'brand': 'Brand'},
            color='return_rate',
            color_continuous_scale='Oranges'
        )
        fig_brand_return.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_brand_return, use_container_width=True)

    # Return rate distribution
    st.subheader("Return Rate Distribution")

    fig_return_dist = px.histogram(
        product_stats[product_stats['total_sales_count'] >= min_sales_for_return],
        x='return_rate',
        nbins=30,
        title=f'Distribution of Return Rates (Products with ≥{min_sales_for_return} sales)',
        labels={'return_rate': 'Return Rate (%)', 'count': 'Number of Products'},
        color_discrete_sequence=['#FF6B6B']
    )
    st.plotly_chart(fig_return_dist, use_container_width=True)

    # Scatter: Sales vs Return Rate
    st.subheader("Sales Volume vs Return Rate")

    scatter_df = product_stats[product_stats['total_sales_count'] >= min_sales_for_return].copy()

    fig_scatter = px.scatter(
        scatter_df,
        x='total_sales_count',
        y='return_rate',
        color='category',
        size='total_revenue',
        hover_data=['name', 'brand'],
        title='Relationship between Sales Volume and Return Rate',
        labels={'total_sales_count': 'Total Sales Count', 'return_rate': 'Return Rate (%)'},
        opacity=0.6
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with tab3:
    st.header("Profit Analysis")
    st.markdown("Identify unprofitable or low-margin products")

    # Filter options
    col1, col2 = st.columns(2)

    with col1:
        profit_filter = st.selectbox(
            "Show Products",
            ["All Products", "Negative Profit", "Profit Margin < 10%", "Profit Margin < 20%"]
        )

    with col2:
        min_sales_profit = st.slider(
            "Minimum Sales for Analysis",
            min_value=1,
            max_value=20,
            value=5,
            step=1
        )

    # Apply filters
    profit_df = product_stats[product_stats['total_sales_count'] >= min_sales_profit].copy()

    if profit_filter == "Negative Profit":
        profit_df = profit_df[profit_df['total_profit'] < 0]
    elif profit_filter == "Profit Margin < 10%":
        profit_df = profit_df[profit_df['profit_margin'] < 10]
    elif profit_filter == "Profit Margin < 20%":
        profit_df = profit_df[profit_df['profit_margin'] < 20]

    profit_df = profit_df.sort_values('total_profit', ascending=True)

    st.info(f"Found **{len(profit_df):,}** products matching criteria")

    # Display table
    st.subheader("Low Profit Products (Top 100)")

    display_df = profit_df.head(100)[['name', 'category', 'brand', 'total_sales_count', 'total_revenue', 'cost', 'avg_sale_price', 'profit_per_item', 'total_profit', 'profit_margin']]

    st.dataframe(
        display_df.style.format({
            'total_sales_count': '{:,.0f}',
            'total_revenue': '${:,.2f}',
            'cost': '${:.2f}',
            'avg_sale_price': '${:.2f}',
            'profit_per_item': '${:.2f}',
            'total_profit': '${:,.2f}',
            'profit_margin': '{:.2f}%'
        }),
        use_container_width=True,
        height=400
    )

    # Visualizations
    st.subheader("Profit Visualizations")

    col1, col2 = st.columns(2)

    with col1:
        # Worst profit products
        worst_profit = profit_df.head(20)

        fig_profit = px.bar(
            worst_profit,
            x='total_profit',
            y='name',
            orientation='h',
            title='Top 20 Products by Lowest Total Profit',
            labels={'total_profit': 'Total Profit ($)', 'name': 'Product'},
            color='total_profit',
            color_continuous_scale='RdYlGn'
        )
        fig_profit.update_layout(yaxis={'categoryorder': 'total ascending'}, height=600)
        st.plotly_chart(fig_profit, use_container_width=True)

    with col2:
        # Profit margin distribution
        fig_margin = px.histogram(
            product_stats[product_stats['total_sales_count'] >= min_sales_profit],
            x='profit_margin',
            nbins=40,
            title=f'Profit Margin Distribution (Products with ≥{min_sales_profit} sales)',
            labels={'profit_margin': 'Profit Margin (%)', 'count': 'Number of Products'},
            color_discrete_sequence=['#4ECDC4']
        )
        st.plotly_chart(fig_margin, use_container_width=True)

        # Category profit
        category_profit = product_stats.groupby('category').agg({
            'total_profit': 'sum'
        }).reset_index().sort_values('total_profit', ascending=True).head(10)

        fig_cat_profit = px.bar(
            category_profit,
            x='total_profit',
            y='category',
            orientation='h',
            title='Bottom 10 Categories by Total Profit',
            labels={'total_profit': 'Total Profit ($)', 'category': 'Category'},
            color='total_profit',
            color_continuous_scale='Reds'
        )
        fig_cat_profit.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_cat_profit, use_container_width=True)

st.divider()

# Export section
st.header("📥 Export Data")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Download Low Sales Products"):
        csv = low_sales_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"low_sales_products_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

with col2:
    if st.button("Download High Return Products"):
        csv = high_return_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"high_return_products_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

with col3:
    if st.button("Download Low Profit Products"):
        csv = profit_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"low_profit_products_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
