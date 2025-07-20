import streamlit as st
import pandas as pd
import snowflake.connector
import plotly.express as px

st.title("Axelar Network Performance Analysis")

# اتصال به Snowflake (اطلاعات در Secrets ذخیره می‌شود)
conn = snowflake.connector.connect(
    user=st.secrets["snowflake"]["user"],
    password=st.secrets["snowflake"]["password"],
    account=st.secrets["snowflake"]["account"],
    warehouse="SNOWFLAKE_LEARNING_WH",
    database="AXELAR",
    schema="PUBLIC"
)

@st.cache_data
def load_data():
    query = """
    select date_trunc('month',block_timestamp) as "Date",
           count(distinct tx_id) as "TXs Count",
           tx_succeeded as "TX Success"
    from AXELAR.CORE.FACT_TRANSACTIONS
    where block_timestamp::date >= '2022-01-01'
    group by 1,3
    order by 1
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

df = load_data()

st.subheader("Transaction Stats per Month (By Success)")
st.write(df.head())

# نمودار ستونی ساده
fig = px.bar(df, x="Date", y="TXs Count", color="TX Success",
             title="Number of Transactions Based on Success Over Time")
st.plotly_chart(fig)

# 1. نمودار خطی
fig_line = px.line(df, x="Date", y="TXs Count", color="TX Success",
                   title="Transaction Trend Over Time",
                   markers=True)
st.plotly_chart(fig_line)

# 2. نمودار میله‌ای گروه‌بندی‌شده
fig_grouped = px.bar(df, x="Date", y="TXs Count", color="TX Success",
                     barmode="group",
                     title="Monthly Transactions by Success/Failure")
st.plotly_chart(fig_grouped)

# 3. نمودار پشته‌ای (Stacked Area Chart)
fig_area = px.area(df, x="Date", y="TXs Count", color="TX Success",
                   title="Cumulative Transactions Over Time (Stacked by Success)")
st.plotly_chart(fig_area)

# 4. نمودار دایره‌ای (Pie Chart) برای کل داده‌ها
summary = df.groupby("TX Success")["TXs Count"].sum().reset_index()
fig_pie = px.pie(summary, names="TX Success", values="TXs Count",
                 title="Success vs Failed Transactions (Total)")
st.plotly_chart(fig_pie)

# 5. نمودار ستونی افقی (Horizontal Bar Chart)
fig_hbar = px.bar(df, y="Date", x="TXs Count", color="TX Success",
                  orientation='h',
                  title="Horizontal Bar Chart of Transactions by Month")
st.plotly_chart(fig_hbar)
