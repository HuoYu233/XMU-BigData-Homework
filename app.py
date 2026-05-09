"""Olist 巴西电商数据智能体 — Streamlit Web 界面"""
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import AgentPipeline

st.set_page_config(
    page_title="Olist 数据智能体",
    page_icon="🛒",
    layout="wide",
)

st.title("🛒 Olist 巴西电商数据智能体")
st.markdown("基于自然语言的电商经营分析助手 — 输入问题，获取数据洞察")

PRESET_QUESTIONS = [
    "每个月的订单量是多少？",
    "各州的订单分布如何？",
    "销售额最高的10个商品类目是什么？",
    "不同支付方式的订单数量和平均支付金额有什么差异？",
    "延迟送达订单的比例是多少？",
    "延迟送达的订单平均评分是否更低？",
    "平均评分最高的5个商品类目是什么？",
]

with st.sidebar:
    st.header("⚙️ 设置")

    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key:
        api_key = st.text_input("DeepSeek API Key", type="password")
        if api_key:
            os.environ["DEEPSEEK_API_KEY"] = api_key

    st.divider()

    st.header("📋 预设问题")
    for q in PRESET_QUESTIONS:
        if st.button(q, use_container_width=True):
            st.session_state["question"] = q

    st.divider()
    st.caption("数据集: Olist Brazilian E-Commerce")
    st.caption("技术栈: MySQL + DeepSeek + LangChain + Streamlit")

question = st.text_area(
    "💬 请输入业务分析问题",
    value=st.session_state.get("question", ""),
    height=80,
    placeholder="例如：销售额最高的10个商品类目是什么？",
)

col1, col2 = st.columns([1, 6])
with col1:
    run_btn = st.button("🔍 查询", type="primary", use_container_width=True)


def render_chart(result, st_module):
    """Render appropriate chart based on query result structure."""
    cols = result["columns"]
    rows = result["rows"]
    df = pd.DataFrame(rows, columns=cols)

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    non_numeric_cols = [c for c in cols if c not in numeric_cols]

    if len(numeric_cols) == 0:
        st_module.info("查询结果不包含数值列，无法自动生成图表")
        return

    fig, ax = plt.subplots(figsize=(10, 5))

    if len(non_numeric_cols) >= 1 and len(numeric_cols) >= 1:
        cat_col = non_numeric_cols[0]
        val_col = numeric_cols[0]
        labels = df[cat_col].astype(str).apply(
            lambda x: x[:20] + "..." if len(str(x)) > 20 else str(x)
        )
        ax.bar(range(len(df)), df[val_col], color="#4ECDC4", edgecolor="#333")
        ax.set_xticks(range(len(df)))
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
        ax.set_ylabel(val_col)
        ax.set_title(f"{val_col} by {cat_col}", fontsize=14, fontweight="bold")
        ax.grid(axis="y", alpha=0.3)
    elif len(numeric_cols) >= 1:
        val_col = numeric_cols[0]
        if len(df) > 1:
            ax.plot(df.index, df[val_col], marker="o", color="#FF6B6B", linewidth=2)
            ax.set_xlabel("Row")
            ax.set_ylabel(val_col)
            ax.set_title(val_col, fontsize=14, fontweight="bold")
            ax.grid(alpha=0.3)
        else:
            ax.bar([0], [df[val_col].iloc[0]], color="#4ECDC4")
            ax.set_xticks([])
            ax.set_ylabel(val_col)
            ax.set_title(val_col, fontsize=14, fontweight="bold")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    st_module.pyplot(fig)
    plt.close(fig)


if run_btn and question.strip():
    pipeline = AgentPipeline()

    try:
        pipeline.connect()

        with st.spinner("正在分析..."):
            result = pipeline.run(question.strip())

        with st.expander("📋 执行过程", expanded=True):
            st.markdown("**① 问题理解 — 识别的相关表**")
            if result["selected_tables"]:
                st.markdown(" | ".join(f"`{t}`" for t in result["selected_tables"]))
            else:
                st.warning("未能识别相关表")

            st.markdown("**② SQL 生成**")
            if result["sql"]:
                st.code(result["sql"], language="sql")
            else:
                st.error("SQL 生成失败")

            st.markdown("**③ 安全检查**")
            if "✅" in result["security_check"]:
                st.success(result["security_check"])
            else:
                st.error(result["security_check"])

            st.markdown(f"**④ 查询执行 (重试次数: {result['retry_count']})**")
            if result["error"]:
                st.error(f"执行失败: {result['error']}")
            elif result["rows"]:
                st.success(f"返回 {len(result['rows'])} 行数据")
                if result["columns"] and result["rows"]:
                    df_result = pd.DataFrame(result["rows"], columns=result["columns"])
                    st.dataframe(df_result, use_container_width=True)

            st.markdown("**⑤ 结果分析**")
            if result["interpretation"]:
                st.info(result["interpretation"])

        if result["rows"] and len(result["rows"]) >= 1:
            with st.expander("📈 可视化图表", expanded=True):
                render_chart(result, st)

    finally:
        pipeline.close()

elif run_btn and not question.strip():
    st.warning("请输入一个问题")
