
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 页面基础设置
st.set_page_config(page_title="PLAB 每日技术面与机构资金分析", layout="wide")
st.title("📈 Photronics Inc (PLAB) 每日技术面 & 机构资金量化终端")

ticker_symbol = "PLAB"
ticker = yf.Ticker(ticker_symbol)

# 获取近 6 个月历史行情数据以保证均线与指标精确
df = ticker.history(period="6mo")

if not df.empty:
    # ------------------ 1. 技术指标与资金流计算 ------------------
    # 均线系统
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA30'] = df['Close'].rolling(30).mean()

    # RSI 指标 (14日)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-10)
    df['RSI'] = 100 - (100 / (1 + rs))

    # OBV 能量潮（机构筹码吸筹指标）
    df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()

    # CMF 佳庆资金流 (20日资金流向)
    mfv = ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / (df['High'] - df['Low'] + 1e-10)
    df['CMF'] = (mfv * df['Volume']).rolling(20).sum() / df['Volume'].rolling(20).sum()

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    # ------------------ 2. 交易额与换手率计算 ------------------
    info = ticker.info
    shares_outstanding = info.get('sharesOutstanding', 59000000)
    inst_holding_pct = info.get('heldPercentInstitutions', 0) * 100

    # 当日交易额 (美元)
    daily_trading_value = latest['Volume'] * ((latest['High'] + latest['Low'] + latest['Close']) / 3)
    # 换手率 (%)
    turnover_rate = (latest['Volume'] / shares_outstanding) * 100
    # 涨跌幅 (%)
    change_pct = ((latest['Close'] - prev['Close']) / prev['Close']) * 100

    # ------------------ 3. 机构进场评分逻辑 ------------------
    score = 0
    signals = []

    # 维度 A: 机构基础持仓率
    if inst_holding_pct > 70:
        score += 30
        signals.append("✅ **机构高度控盘**：机构持仓占比 > 70%，属于主力核心关注标的。")
    elif inst_holding_pct > 50:
        score += 20
        signals.append("🟡 **机构中度参与**：机构持仓占比在 50% - 70% 之间。")
    else:
        signals.append("❌ **散户主导/机构参与度低**：机构持仓 < 50%。")

    # 维度 B: CMF 佳庆资金流
    cmf_val = latest['CMF']
    if cmf_val > 0.15:
        score += 35
        signals.append(f"🔥 **主力强劲吸筹**：CMF 资金流为 `{cmf_val:.2f}` (>0.15)，大资金净流入极其明显。")
    elif cmf_val > 0:
        score += 20
        signals.append(f"🟢 **温和资金流入**：CMF 资金流为 `{cmf_val:.2f}` (>0)，有资金默默潜伏。")
    else:
        signals.append(f"⚠️ **资金流出形态**：CMF 资金流为 `{cmf_val:.2f}` (<0)，大资金呈净流出状态。")

    # 维度 C: OBV 与 20日均线匹配度
    obv_ma10 = df['OBV'].tail(10).mean()
    if latest['OBV'] > obv_ma10 and latest['Close'] >= latest['MA20']:
        score += 35
        signals.append("📈 **量价齐升**：OBV 能量潮向上突破，且股价稳居 MA20 支撑位上方。")
    else:
        signals.append("📉 **量能未企稳**：OBV 在底部震荡或突破受阻，等待量能释放。")

    # ------------------ 4. Streamlit 界面渲染 ------------------

    # 第一板块：每日关键指标看板
    st.subheader("📌 每日行情与流动性数据看板")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("最新收盘价", f"${latest['Close']:.2f}", f"{change_pct:+.2f}%")
    col2.metric("当日交易额", f"${daily_trading_value / 1e6:.2f} M")
    col3.metric("换手率 (Turnover)", f"{turnover_rate:.2f}%")
    col4.metric("CMF 资金流 (20日)", f"{cmf_val:.2f}")

    st.markdown("---")

    # 第二板块：机构进场诊断
    st.subheader("🕵️ 机构资金 (Smart Money) 进场诊断")
    if score >= 75:
        st.success(f"🎯 **诊断结论：机构已明显进场吸筹（综合评分：{score}/100）**")
    elif score >= 50:
        st.warning(f"👀 **诊断结论：机构试探性建仓 / 震荡洗盘中（综合评分：{score}/100）**")
    else:
        st.error(f"🛑 **诊断结论：机构未明显进场 / 以散户观望为主（综合评分：{score}/100）**")

    for sig in signals:
        st.write(sig)

    st.markdown("---")

    # 第三板块：技术面图表分析
    st.subheader("📊 均线系统 (MA5 / MA10 / MA20 / MA30)")
    st.line_chart(df[['Close', 'MA5', 'MA10', 'MA20', 'MA30']].tail(60))

    col_rsi, col_cmf = st.columns(2)
    with col_rsi:
        st.subheader("📈 RSI 强弱指标 (14日)")
        st.line_chart(df[['RSI']].tail(60))
        st.caption("提示：RSI > 70 为超买，RSI < 30 为超卖（当前值：" + f"{latest['RSI']:.2f}）")

    with col_cmf:
        st.subheader("🌊 CMF 佳庆资金流指标")
        st.line_chart(df[['CMF']].tail(60))
        st.caption("提示：>0 代表买方主导，<0 代表卖方主导（当前值：" + f"{cmf_val:.2f}）")

    # 第四板块：2,000 美元风控策略执行面板
    st.markdown("---")
    st.subheader("💡 2,000 美元风控建仓参考")
    c1, c2, c3 = st.columns(3)
    c1.info(f"**建议买入区间**\n\n${latest['MA20']:.2f} -${latest['MA5']:.2f}")
    c2.error("**止损底线**\n\n$26.80（破位严格退场）")
    c3.success("**止盈目标**\n\n第一目标: $32.50\n\n第二目标: $36.00")

else:
    st.error("未能获取到 PLAB 的股票数据，请稍后再试。")
