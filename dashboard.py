import streamlit as st
import pandas as pd
import snowflake.connector
import plotly.express as px

st.title("داشبورد Snowflake با Streamlit")

# اتصال به Snowflake (اطلاعات در Secrets ذخیره می‌شود)
conn = snowflake.connector.connect(
    user=st.secrets["snowflake"]["user"],
    password=st.secrets["snowflake"]["password"],
    account=st.secrets["snowflake"]["account"],
    warehouse="SNOWFLAKE_LEARNING_WH",
    database="YOUR_DATABASE",
    schema="YOUR_SCHEMA"
)

@st.cache_data
def load_data():
    query = "SELECT * FROM YOUR_TABLE LIMIT 1000;"
    return pd.read_sql(query, conn)

df = load_data()

st.subheader("نمونه داده‌ها")
st.write(df.head())

# رسم یک نمودار ساده ستونی
fig = px.bar(df, x=df.columns[0], y=df.columns[1], title="نمودار ستونی نمونه")
st.plotly_chart(fig)
