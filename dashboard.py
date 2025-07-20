import streamlit as st
import pandas as pd
import snowflake.connector
import plotly.express as px

st.title("Axelar Network Performance Analysis")

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

# انتخاب Time Frame
timeframe = st.selectbox("Select Time Frame", ["day", "week", "month"])

# انتخاب بازه زمانی
start_date = st.date_input("Start Date", value=pd.to_datetime("2022-01-01"))
end_date = st.date_input("End Date", value=pd.to_datetime("today"))

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

# اجرای کوئری‌ها
df = load_main_data(timeframe, start_date, end_date)
success_rate = load_success_rate(start_date, end_date)
total_txs = load_total_txs(start_date, end_date)

# ردیف اول: نمایش متریک‌ها
col1, col2 = st.columns(2)
col1.metric(label="Current Success Rate of Transactions", value=f"{success_rate}%")
col2.metric(label="Total Transactions Count", value=f"{total_txs:,}")

# ردیف دوم: نمودار ستونی (Bar Chart)
fig_bar = px.bar(df, x="Date", y="TXs Count", color="TX Success",
                 title="Number of Transactions Based on Success Over Time")
st.plotly_chart(fig_bar)

# ردیف سوم: نمودار نرمال شده و نمودار دایره‌ای کنار هم
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
