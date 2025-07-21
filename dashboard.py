import streamlit as st
import pandas as pd
import snowflake.connector
import plotly.express as px

st.title("Axelar Network Performance Analysis")

# توضیحات پایین عنوان
st.markdown("""
### About Axelar
Axelar Network is a decentralized blockchain platform designed to enable seamless interoperability between disparate blockchain ecosystems. 
Launched to address the fragmentation in the blockchain space, Axelar provides a robust infrastructure for cross-chain communication, 
allowing different blockchains to securely share data and transfer assets. By leveraging a decentralized network of validators and 
a universal protocol, Axelar facilitates scalable, secure, and efficient interactions across blockchains, empowering developers to 
build applications that operate across multiple chains without complex integrations. With its focus on simplifying cross-chain 
connectivity, Axelar aims to drive the adoption of Web3 by creating a unified, interoperable blockchain environment.
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
timeframe = st.selectbox("Select Time Frame", ["day", "week", "month"])
start_date = st.date_input("Start Date", value=pd.to_datetime("2022-01-01"))
end_date = st.date_input("End Date", value=pd.to_datetime("today"))

# --- کوئری‌ها ---

@st.cache_data
def load_main_data(timeframe, start_date, end_date):
    query = f"""
    SELECT date_trunc('{timeframe}', block_timestamp) AS "Date",
           COUNT(DISTINCT tx_id) AS "TXs Count",
           tx_succeeded AS "TX Success"
    FROM AXELAR.CORE.FACT_TRANSACTIONS
    WHERE block_timestamp::date >= '{start_date}'
      AND block_timestamp::date <= '{end_date}'
    GROUP BY 1, 3
    ORDER BY 1
    """
    return pd.read_sql(query, conn)

@st.cache_data
def load_success_rate(start_date, end_date):
    query = f"""
    WITH TAB1 AS (
        SELECT COUNT(DISTINCT tx_id) AS "Succeeded TXs Count"
        FROM axelar.core.fact_transactions
        WHERE block_timestamp::date >= '{start_date}'
          AND block_timestamp::date <= '{end_date}'
          AND tx_succeeded = 'TRUE'
    ),
    TAB2 AS (
        SELECT COUNT(DISTINCT tx_id) AS "Total TXs Count"
        FROM axelar.core.fact_transactions
        WHERE block_timestamp::date >= '{start_date}'
          AND block_timestamp::date <= '{end_date}'
    )
    SELECT ROUND((("Succeeded TXs Count"/"Total TXs Count")*100),2) AS "Success Rate"
    FROM TAB1, TAB2
    """
    return pd.read_sql(query, conn).iloc[0, 0]

@st.cache_data
def load_total_txs(start_date, end_date):
    query = f"""
    SELECT COUNT(DISTINCT tx_id) AS "TXs Count"
    FROM axelar.core.fact_transactions
    WHERE block_timestamp::date >= '{start_date}'
      AND block_timestamp::date <= '{end_date}'
    """
    return pd.read_sql(query, conn).iloc[0, 0]

@st.cache_data
def load_tps_data(timeframe, start_date, end_date):
    query = f"""
    WITH tab1 AS (
        SELECT block_timestamp::date AS date,
               COUNT(DISTINCT tx_id) / 86400 AS TPS
        FROM axelar.core.fact_transactions
        WHERE tx_succeeded = 'true'
          AND block_timestamp::date >= '{start_date}'
          AND block_timestamp::date <= '{end_date}'
        GROUP BY 1
    )
    SELECT date_trunc('{timeframe}', date) AS "Date",
           ROUND(AVG(tps), 2) AS TPS
    FROM tab1
    GROUP BY 1
    ORDER BY 1
    """
    return pd.read_sql(query, conn)

@st.cache_data
def load_correlation_data(start_date, end_date):
    query = f"""
    WITH tab1 AS (
        SELECT block_timestamp::date AS date,
               COUNT(DISTINCT tx_id) AS total_tx_count
        FROM axelar.core.fact_transactions
        WHERE block_timestamp::date >= '{start_date}'
          AND block_timestamp::date <= '{end_date}'
        GROUP BY 1
    ),
    tab2 AS (
        SELECT block_timestamp::date AS date,
               COUNT(DISTINCT tx_id) AS false_tx_count
        FROM axelar.core.fact_transactions
        WHERE block_timestamp::date >= '{start_date}'
          AND block_timestamp::date <= '{end_date}'
          AND tx_succeeded = 'false'
        GROUP BY 1
    )
    SELECT corr(total_tx_count, false_tx_count) AS cc
    FROM tab1 LEFT JOIN tab2 ON tab1.date = tab2.date
    """
    return pd.read_sql(query, conn).iloc[0, 0]

# --- اجرای کوئری‌ها ---
df = load_main_data(timeframe, start_date, end_date)
success_rate = load_success_rate(start_date, end_date)
total_txs = load_total_txs(start_date, end_date)
df_tps = load_tps_data(timeframe, start_date, end_date)
correlation_value = load_correlation_data(start_date, end_date)

# --- ردیف اول: نمایش متریک‌ها ---
col1, col2 = st.columns(2)
col1.metric(label="Current Success Rate of Transactions", value=f"{success_rate}%")
col2.metric(label="Total Transactions Count", value=f"{total_txs:,}")

# --- ردیف دوم: نمودار ستونی (Bar Chart) ---
fig_bar = px.bar(df, x="Date", y="TXs Count", color="TX Success",
                 title="Number of Transactions Based on Success Over Time")
st.plotly_chart(fig_bar)

# --- ردیف سوم: نمودار نرمال شده و نمودار دایره‌ای ---
col3, col4 = st.columns(2)

# نمودار نرمال شده (Normalized Stacked Bar Chart)
df_percent = df.copy()
monthly_total = df_percent.groupby("Date")["TXs Count"].transform("sum")
df_percent["Percentage"] = df_percent["TXs Count"] / monthly_total * 100
fig_normalized = px.bar(df_percent, x="Date", y="Percentage", color="TX Success",
                        title="Normalized Transactions by Success (%)",
                        barmode="stack")
col3.plotly_chart(fig_normalized)

# نمودار دایره‌ای (Pie Chart) - Total Transactions Count by Success
summary = df.groupby("TX Success")["TXs Count"].sum().reset_index()
fig_pie = px.pie(summary, names="TX Success", values="TXs Count",
                 title="Success vs Failed Transactions (Total)")
col4.plotly_chart(fig_pie)

# --- ردیف چهارم: نمودار نقطه‌ای (Scatter Plot) - TPS Over Time ---
fig_tps = px.scatter(df_tps, x="Date", y="TPS", size="TPS",
                     title="Transaction Per Second (TPS) Over Time",
                     labels={"TPS": "Transactions Per Second"},
                     color="TPS", color_continuous_scale="Viridis")
st.plotly_chart(fig_tps)

# --- ردیف پنجم: نمایش Correlation Coefficient ---
st.metric(
    label="Effect of Increasing the Number of Transactions on the Number of Failed Transactions (Correlation Coefficient)",
    value=f"{correlation_value:.2f}"
)
