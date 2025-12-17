import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Category Analysis", layout="wide")

st.title("📊 Product Category Sales Analysis")

@st.cache_data
def load_data():
    """Load order items, products, and orders data"""
    order_items_df = pd.read_csv("sample_data/order_items.csv")
    products_df = pd.read_csv("sample_data/products.csv")
    orders_df = pd.read_csv("sample_data/orders.csv")

    # Merge order items with products to get category information
    merged_df = order_items_df.merge(
        products_df[['id', 'category', 'name', 'brand', 'department']],
        left_on='product_id',
        right_on='id',
        how='left'
    )

    # Merge with orders to get gender information
    merged_df = merged_df.merge(
        orders_df[['order_id', 'gender']],
        on='order_id',
        how='left'
    )

    # Convert date columns to datetime
    merged_df['created_at'] = pd.to_datetime(merged_df['created_at'])

    return merged_df, products_df

def get_period_dates(period_type, reference_date):
    """Calculate start and end dates based on period type"""
    if period_type == "Last 7 Days":
        end_date = reference_date
        start_date = end_date - timedelta(days=6)
    elif period_type == "Last 30 Days":
        end_date = reference_date
        start_date = end_date - timedelta(days=29)
    elif period_type == "This Month":
        start_date = reference_date.replace(day=1)
        end_date = reference_date
    elif period_type == "Last Month":
        first_day_this_month = reference_date.replace(day=1)
        end_date = first_day_this_month - timedelta(days=1)
        start_date = end_date.replace(day=1)
    elif period_type == "This Quarter":
        quarter = (reference_date.month - 1) // 3
        start_date = datetime(reference_date.year, quarter * 3 + 1, 1).date()
        end_date = reference_date
    elif period_type == "Last Quarter":
        first_day_this_quarter = datetime(reference_date.year, ((reference_date.month - 1) // 3) * 3 + 1, 1).date()
        end_date = first_day_this_quarter - timedelta(days=1)
        quarter = (end_date.month - 1) // 3
        start_date = datetime(end_date.year, quarter * 3 + 1, 1).date()
    elif period_type == "This Year":
        start_date = datetime(reference_date.year, 1, 1).date()
        end_date = reference_date
    elif period_type == "Last Year":
        start_date = datetime(reference_date.year - 1, 1, 1).date()
        end_date = datetime(reference_date.year - 1, 12, 31).date()
    else:  # All Time
        return None, None

    return start_date, end_date

# Load data
merged_df, products_df = load_data()

# Sidebar filters
st.sidebar.header("Filters")

# Period selection
st.sidebar.subheader("📅 Analysis Period")
period_type = st.sidebar.selectbox(
    "Select Period",
    ["All Time", "Last 7 Days", "Last 30 Days", "This Month", "Last Month",
     "This Quarter", "Last Quarter", "This Year", "Last Year", "Custom Range"],
    index=0
)

# Get min and max dates from data
min_date = merged_df['created_at'].min().date()
max_date = merged_df['created_at'].max().date()

# Calculate date range based on period type
if period_type == "Custom Range":
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    if len(date_range) == 2:
        start_date, end_date = date_range[0], date_range[1]
    else:
        start_date, end_date = min_date, max_date
else:
    start_date, end_date = get_period_dates(period_type, max_date)
    if start_date is None:
        start_date, end_date = min_date, max_date

# Display selected period
if period_type != "All Time":
    st.sidebar.info(f"📊 Analyzing: {start_date} to {end_date}")
else:
    st.sidebar.info(f"📊 Analyzing: All available data")

st.sidebar.divider()

# Status filter
st.sidebar.subheader("🔍 Status Filter")
status_options = ['All'] + list(merged_df['status'].unique())
selected_status = st.sidebar.selectbox("Order Status", status_options)

st.sidebar.divider()

# Gender filter
st.sidebar.subheader("👥 Gender Filter")
selected_gender = st.sidebar.radio(
    "Select Gender",
    options=["All", "Male", "Female"],
    index=0,
    horizontal=True
)

# Apply filters
filtered_df = merged_df.copy()

# Apply status filter
if selected_status != 'All':
    filtered_df = filtered_df[filtered_df['status'] == selected_status]

# Apply gender filter
if selected_gender == "Male":
    filtered_df = filtered_df[filtered_df['gender'] == 'M']
elif selected_gender == "Female":
    filtered_df = filtered_df[filtered_df['gender'] == 'F']

# Apply date filter
if period_type != "All Time":
    filtered_df = filtered_df[
        (filtered_df['created_at'].dt.date >= start_date) &
        (filtered_df['created_at'].dt.date <= end_date)
    ]

# Calculate category metrics
category_metrics = filtered_df.groupby('category').agg({
    'sale_price': ['sum', 'mean', 'count'],
    'id_x': 'count'
}).round(2)

category_metrics.columns = ['Total Sales', 'Avg Price', 'Count_1', 'Order Count']
category_metrics = category_metrics[['Total Sales', 'Avg Price', 'Order Count']]
category_metrics = category_metrics.sort_values('Total Sales', ascending=False)

# Add percentage of total sales
category_metrics['Sales %'] = (
    category_metrics['Total Sales'] / category_metrics['Total Sales'].sum() * 100
).round(2)

# Display period summary
filter_info = f"**Gender:** {selected_gender}"
if selected_status != 'All':
    filter_info += f" | **Status:** {selected_status}"

if period_type != "All Time":
    total_days = (end_date - start_date).days + 1
    st.info(f"📅 **Analysis Period:** {period_type} ({start_date} to {end_date}) - {total_days} days | **Records:** {len(filtered_df):,} orders | {filter_info}")
else:
    st.info(f"📅 **Analysis Period:** {period_type} | **Records:** {len(filtered_df):,} orders | {filter_info}")

# Overview metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Sales",
        f"${category_metrics['Total Sales'].sum():,.2f}"
    )

with col2:
    st.metric(
        "Total Categories",
        len(category_metrics)
    )

with col3:
    st.metric(
        "Total Orders",
        f"{category_metrics['Order Count'].sum():,.0f}"
    )

with col4:
    st.metric(
        "Avg Order Value",
        f"${category_metrics['Total Sales'].sum() / category_metrics['Order Count'].sum():.2f}"
    )

st.divider()

# Display category metrics table
st.header("Category Performance Summary")
st.dataframe(
    category_metrics.style.format({
        'Total Sales': '${:,.2f}',
        'Avg Price': '${:.2f}',
        'Order Count': '{:,.0f}',
        'Sales %': '{:.2f}%'
    }),
    use_container_width=True
)

st.divider()

# Visualizations
col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 10 Categories by Sales")
    top_10_categories = category_metrics.head(10)

    fig_bar = px.bar(
        top_10_categories.reset_index(),
        x='Total Sales',
        y='category',
        orientation='h',
        title='Top 10 Categories by Total Sales',
        labels={'Total Sales': 'Total Sales ($)', 'category': 'Category'},
        color='Total Sales',
        color_continuous_scale='Blues'
    )
    fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    st.subheader("Sales Distribution by Category")
    top_5_categories = category_metrics.head(5)

    fig_pie = px.pie(
        top_5_categories.reset_index(),
        values='Total Sales',
        names='category',
        title='Top 5 Categories Sales Distribution',
        hole=0.4
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# Order count and average price comparison
col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 10 Categories by Order Count")
    top_10_by_count = category_metrics.sort_values('Order Count', ascending=False).head(10)

    fig_count = px.bar(
        top_10_by_count.reset_index(),
        x='Order Count',
        y='category',
        orientation='h',
        title='Top 10 Categories by Order Count',
        labels={'Order Count': 'Number of Orders', 'category': 'Category'},
        color='Order Count',
        color_continuous_scale='Greens'
    )
    fig_count.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_count, use_container_width=True)

with col2:
    st.subheader("Average Price by Category")
    top_10_by_price = category_metrics.sort_values('Avg Price', ascending=False).head(10)

    fig_price = px.bar(
        top_10_by_price.reset_index(),
        x='Avg Price',
        y='category',
        orientation='h',
        title='Top 10 Categories by Average Price',
        labels={'Avg Price': 'Average Price ($)', 'category': 'Category'},
        color='Avg Price',
        color_continuous_scale='Oranges'
    )
    fig_price.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_price, use_container_width=True)

st.divider()

# Time series analysis
st.header("Sales Trends Over Time")

# Allow user to select categories for trend analysis
all_categories = sorted(filtered_df['category'].unique())
selected_categories = st.multiselect(
    "Select categories to compare (max 5)",
    all_categories,
    default=list(category_metrics.head(5).index)
)

if selected_categories:
    trend_df = filtered_df[filtered_df['category'].isin(selected_categories)].copy()
    trend_df['date'] = trend_df['created_at'].dt.date

    daily_sales = trend_df.groupby(['date', 'category'])['sale_price'].sum().reset_index()

    fig_trend = px.line(
        daily_sales,
        x='date',
        y='sale_price',
        color='category',
        title='Daily Sales Trend by Category',
        labels={'sale_price': 'Sales ($)', 'date': 'Date', 'category': 'Category'}
    )
    fig_trend.update_layout(hovermode='x unified')
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.info("Please select at least one category to view the trend.")

st.divider()

# Department analysis
st.header("Department Analysis")

dept_metrics = filtered_df.groupby('department').agg({
    'sale_price': 'sum',
    'id_x': 'count'
}).round(2)
dept_metrics.columns = ['Total Sales', 'Order Count']
dept_metrics = dept_metrics.sort_values('Total Sales', ascending=False)

col1, col2 = st.columns(2)

with col1:
    fig_dept_sales = px.bar(
        dept_metrics.reset_index(),
        x='department',
        y='Total Sales',
        title='Sales by Department',
        labels={'Total Sales': 'Total Sales ($)', 'department': 'Department'},
        color='Total Sales',
        color_continuous_scale='Purples'
    )
    st.plotly_chart(fig_dept_sales, use_container_width=True)

with col2:
    fig_dept_pie = px.pie(
        dept_metrics.reset_index(),
        values='Total Sales',
        names='department',
        title='Department Sales Distribution',
        hole=0.4
    )
    st.plotly_chart(fig_dept_pie, use_container_width=True)

# Show department metrics table
st.subheader("Department Performance")
st.dataframe(
    dept_metrics.style.format({
        'Total Sales': '${:,.2f}',
        'Order Count': '{:,.0f}'
    }),
    use_container_width=True
)
