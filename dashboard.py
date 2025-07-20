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
def load_data(timeframe, start_date, end_date):
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

df = load_data(timeframe, start_date, end_date)

st.subheader("Transaction Stats per Selected Period (By Success)")
st.write(df.head())

# نمودار 1: ستونی ساده
fig_bar = px.bar(df, x="Date", y="TXs Count", color="TX Success",
                 title="Number of Transactions Based on Success Over Time")
st.plotly_chart(fig_bar)

# نمودار 2: خطی
fig_line = px.line(df, x="Date", y="TXs Count", color="TX Success",
                   title="Transactions Trend Over Time")
st.plotly_chart(fig_line)

# نمودار 3: مساحت
fig_area = px.area(df, x="Date", y="TXs Count", color="TX Success",
                   title="Area Chart of Transactions Over Time")
st.plotly_chart(fig_area)

# نمودار 4: هیستوگرام
fig_hist = px.histogram(df, x="Date", y="TXs Count", color="TX Success",
                        title="Histogram of Transactions")
st.plotly_chart(fig_hist)

# نمودار 5: ستونی نرمالیزه‌شده (درصدی)
df_percent = df.copy()
monthly_total = df_percent.groupby("Date")["TXs Count"].transform("sum")
df_percent["Percentage"] = df_percent["TXs Count"] / monthly_total * 100
fig_normalized = px.bar(df_percent, x="Date", y="Percentage", color="TX Success",
                        title="Normalized Monthly Transactions by Success (%)",
                        barmode="stack")
st.plotly_chart(fig_normalized)
