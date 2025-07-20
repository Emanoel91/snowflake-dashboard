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
    query = """select date_trunc('month',block_timestamp) as "Date", count(distinct tx_id) as "TXs Count", 
tx_succeeded as "TX Success"
from AXELAR.CORE.FACT_TRANSACTIONS
where block_timestamp::date>='2022-01-01'
group by 1,3
order by 1"""
    return pd.read_sql(query, conn)

df = load_data()

st.subheader("نمونه داده‌ها")
st.write(df.head())

# رسم یک نمودار ساده ستونی
fig = px.bar(df, x=df.columns[0], y=df.columns[1], title="نمودار ستونی نمونه")
st.plotly_chart(fig)
