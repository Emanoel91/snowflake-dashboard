import streamlit as st
import pandas as pd
import snowflake.connector
import plotly.express as px

st.title("Axelar Network Performance Analysis")

# توضیحات زیر عنوان
st.write("""
Axelar Network is a decentralized blockchain platform designed to enable seamless interoperability 
between disparate blockchain ecosystems. Launched to address the fragmentation in the blockchain space, 
Axelar provides a robust infrastructure for cross-chain communication, allowing different blockchains 
to securely share data and transfer assets. By leveraging a decentralized network of validators and 
a universal protocol, Axelar facilitates scalable, secure, and efficient interactions across blockchains, 
empowering developers to build applications that operate across multiple chains without complex integrations.
""")

# اتصال به Snowflake
conn = snowflake.connector.connect(
    user=st.secrets["snowflake"]["user"],
    password=st.secrets["snowflake"]["password"],
    account=st.secrets["snowflake"]["account"],
    warehouse="SNOWFLAKE_LEARNING_WH",
    database="AXELAR",
    schema="PUBLIC"
)

# انتخاب Time Frame و Time Period
time_frame = st.selectbox("Select Time Frame", ["day", "week", "month"])
start_date = st.date_input("Start Date", value=pd.to_datetime("2022-01-01"))
end_date = st.date_input("End Date", value=pd.to_datetime("today"))

# ------------------ داده‌های اصلی ------------------
@st.cache_data
def load_tx_data(time_frame, start_date, end_date):
    query = f"""
        SELECT date_trunc('{time_frame}', block_timestamp) AS "Date",
               COUNT(DISTINCT tx_id) AS "TXs Count",
               tx_succeeded AS "TX Success"
        FROM AXELAR.CORE.FACT_TRANSACTIONS
        WHERE block_timestamp::date >= '{start_date}' AND block_timestamp::date <= '{end_date}'
        GROUP BY 1,3
        ORDER BY 1
    """
    return pd.read_sql(query, conn)

df = load_tx_data(time_frame, start_date, end_date)

# ------------------ متریک‌های بالای صفحه ------------------
@st.cache_data
def load_success_rate(start_date, end_date):
    query = f"""
        WITH TAB1 AS (
            SELECT COUNT(DISTINCT tx_id) AS "Succeeded TXs Count"
            FROM axelar.core.fact_transactions
            WHERE block_timestamp::date >= '{start_date}' AND block_timestamp::date <= '{end_date}'
              AND tx_succeeded = 'TRUE'
        ),
        TAB2 AS (
            SELECT COUNT(DISTINCT tx_id) AS "Total TXs Count"
            FROM axelar.core.fact_transactions
            WHERE block_timestamp::date >= '{start_date}' AND block_timestamp::date <= '{end_date}'
        )
        SELECT ROUND((("Succeeded TXs Count"/"Total TXs Count")*100), 2) AS "Success Rate"
        FROM TAB1, TAB2
    """
    return pd.read_sql(query, conn).iloc[0, 0]

@st.cache_data
def load_total_txs(start_date, end_date):
    query = f"""
        SELECT COUNT(DISTINCT tx_id) AS "TXs Count"
        FROM axelar.core.fact_transactions
        WHERE block_timestamp::date >= '{start_date}' AND block_timestamp::date <= '{end_date}'
    """
    return pd.read_sql(query, conn).iloc[0, 0]

success_rate = load_success_rate(start_date, end_date)
total_txs = load_total_txs(start_date, end_date)

col1, col2 = st.columns(2)
col1.metric("Current Success Rate of Transactions", f"{success_rate}%")
col2.metric("Total Transactions Count", f"{total_txs:,}")

# ------------------ نمودار ستونی ------------------
# Number of Transactions Based on Success Over Time
fig_bar = px.bar(df, x="Date", y="TXs Count", color="TX Success",
                 title="Number of Transactions Based on Success Over Time")
st.plotly_chart(fig_bar, use_container_width=True)

# ------------------ نمودارهای کنار هم ------------------
col3, col4 = st.columns(2)

# نمودار نرمال‌شده (Normalized Stacked Bar Chart)
df_total = df.groupby("Date")["TXs Count"].sum().reset_index()
df_norm = df.merge(df_total, on="Date")
df_norm["Percentage"] = df_norm["TXs Count"] / df_norm["TXs Count_y"] * 100
fig_norm = px.bar(df_norm, x="Date", y="Percentage", color="TX Success",
                  title="Normalized Stacked Bar Chart (Success vs Failed)")
col3.plotly_chart(fig_norm, use_container_width=True)

# نمودار دایره‌ای (Pie Chart) - Total Transactions Count by Success
summary = df.groupby("TX Success")["TXs Count"].sum().reset_index()
fig_pie = px.pie(summary, names="TX Success", values="TXs Count",
                 title="Success vs Failed Transactions (Total)")
col4.plotly_chart(fig_pie, use_container_width=True)

# ------------------ نمودار نقطه‌ای ------------------
@st.cache_data
def load_tps_data(time_frame, start_date, end_date):
    query = f"""
        WITH tab1 AS (
            SELECT block_timestamp::date AS date,
                   COUNT(DISTINCT tx_id) / 86400 AS TPS
            FROM axelar.core.fact_transactions
            WHERE tx_succeeded = 'TRUE'
              AND block_timestamp::date >= '{start_date}'
              AND block_timestamp::date <= '{end_date}'
            GROUP BY 1
        )
        SELECT date_trunc('{time_frame}', date) AS "Date",
               AVG(TPS) AS TPS
        FROM tab1
        GROUP BY 1
        ORDER BY 1
    """
    return pd.read_sql(query, conn)

df_tps = load_tps_data(time_frame, start_date, end_date)
fig_tps = px.scatter(df_tps, x="Date", y="TPS", size="TPS",
                     title="Transaction Per Second (TPS) Over Time")
st.plotly_chart(fig_tps, use_container_width=True)

