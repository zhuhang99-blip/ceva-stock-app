import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="CEVA 股票每日分析助手", layout="wide")
st.title("📈 CEVA Inc (CEVA) 每日技术面与资金流向分析")

ticker = yf.Ticker("CEVA")
df = ticker.history(period="1mo")

if not df.empty:
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA30'] = df['Close'].rolling(30).mean()
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    shares_outstanding = ticker.info.get('sharesOutstanding', 28150000)
    turnover_rate = (latest['Volume'] / shares_outstanding) * 100
    change_pct = ((latest['Close'] - prev['Close']) / prev['Close']) * 100

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("最新收盘价", f"${latest['Close']:.2f}", f"{change_pct:+.2f}%")
    col2.metric("成交量", f"{int(latest['Volume']):,}")
    col3.metric("换手率", f"{turnover_rate:.2f}%")
    col4.metric("MA30 关键线", f"${latest['MA30']:.2f}")

    st.line_chart(df[['Close', 'MA5', 'MA10', 'MA20', 'MA30']])

    st.subheader("💡 2000 美元建仓与风控建议")
    st.write(f"- **第一笔买入区（支撑位）：** $28.70 - $29.00（接近当前 MA5: ${latest['MA5']:.2f}）")
    st.write(f"- **止损底线：** $27.20（跌破跌穿筑底结构）")
    st.write(f"- **第一止盈位：** $32.00")
else:
    st.error("未能抓取到 CEVA 数据，请稍后再试。")
