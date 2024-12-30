import streamlit as st
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from agent.query import QueryProcessor
from agent.stock_analysis import StockAnalyzer

# 加载环境变量
load_dotenv()

# 配置页面
st.set_page_config(
    page_title="股票分析助手",
    page_icon="📈",
    layout="wide"
)

# 标题
st.title("📊 智能股票分析助手")

# 侧边栏配置
with st.sidebar:
    st.header("配置参数")
    
    # LLM模型选择
    chat_model = st.selectbox(
        "选择LLM模型",
        ["deepseek-chat","glm-4-plus"],
        index=0
    )
    
    # Embedding模型配置
    embedding_model_name = "embedding-3"
    embedding_store_dir = ".index_all_embedding_3"

# 主界面
col1, col2 = st.columns([2, 1])

with col1:
    # 股票分析部分
    st.subheader("股票分析")
    
    # 输入部分
    stock_name = st.text_input("输入股票名称", value="贵州茅台")
    
    # 日期选择
    col_date1, col_date2 = st.columns(2)
    with col_date1:
        start_date = st.date_input(
            "开始日期",
            datetime.now() - timedelta(days=30)
        )
    with col_date2:
        end_date = st.date_input(
            "结束日期",
            datetime.now()
        )

    # 分析按钮
    if st.button("开始分析", type="primary"):
        with st.spinner("正在分析中...(可能需要几分钟) "):
            try:
                # 初始化处理器
                processor = QueryProcessor(
                    llm_api_key=os.getenv("zhipu_api_key") if chat_model == "glm-4-plus" else os.getenv("deepseek_api_key"),
                    llm_base_url=os.getenv("zhipu_base_url") if chat_model == "glm-4-plus" else os.getenv("deepseek_base_url"),
                    chat_model=chat_model,
                    embedding_model_name=embedding_model_name,
                    embedding_store_dir=embedding_store_dir,
                    embedding_api_key=os.getenv("zhipu_api_key") ,
                    embedding_base_url=os.getenv("zhipu_base_url")
                )

                # 初始化分析器
                analyzer = StockAnalyzer(processor)

                # 执行分析
                result = analyzer.analyze_stock(
                    stock_name=stock_name,
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d")
                )

                # 获取分析报告
                analysis_result = analyzer.get_stock_report(result)
                
                # 显示结果
                st.success("分析完成！")
                st.markdown("### 分析报告")
                st.write(analysis_result)

            except Exception as e:
                st.error(f"分析过程中出现错误: {str(e)}")

with col2:
    # 使用说明
    st.subheader("使用说明")
    st.markdown("""
    1. 在左侧输入框中输入股票名称
    2. 选择要分析的时间范围
    3. 点击"开始分析"按钮
    4. 等待分析结果生成
    
    **注意事项：**
    - 股票名称请输入完整的名称
    - 时间范围建议不要太长，以获得更精确的分析
    - 分析过程可能需要一些时间，请耐心等待
    """)

# 页脚
st.markdown("---")
st.markdown("### 💡 提示")
st.info("本系统使用AI大模型进行分析，结果仅供参考，不构成投资建议。") 