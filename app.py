import streamlit as st
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 这几个类需要你自己在 agent 包中实现或修改
from agent.query import QueryProcessor
from agent.stock_analysis import StockAnalyzer
from agent.chat_manager import ChatManager

# 加载环境变量
load_dotenv()

# 配置Streamlit页面
st.set_page_config(
    page_title="股票分析助手",
    page_icon="📈",
    layout="wide"
)

# ---- 1. 定义一些辅助函数 ----

def init_query_processor(chat_model: str) -> QueryProcessor:
    """
    根据选择的 LLM 模型，初始化 QueryProcessor。
    不同模型可能需要不同的 API_KEY 或 BASE_URL。
    """
    if chat_model == "glm-4-plus":
        llm_api_key = os.getenv("zhipu_api_key")
        llm_base_url = os.getenv("zhipu_base_url")
    else:  # deepseek-chat
        llm_api_key = os.getenv("deepseek_api_key")
        llm_base_url = os.getenv("deepseek_base_url")
    
    # 这里假设 embedding 使用智谱的API
    embedding_api_key = os.getenv("zhipu_api_key")
    embedding_base_url = os.getenv("zhipu_base_url")
    
    # 如果找不到相关的key，可以做一个简单的提示
    if not llm_api_key or not llm_base_url:
        st.warning("未找到对应模型的API_KEY或BASE_URL，请检查环境变量配置。")
    
    return QueryProcessor(
        llm_api_key=llm_api_key,
        llm_base_url=llm_base_url,
        chat_model=chat_model,
        embedding_model_name="embedding-3",
        embedding_store_dir=".index_all_embedding_3",
        embedding_api_key=embedding_api_key,
        embedding_base_url=embedding_base_url
    )


def analyze_stock_report(processor: QueryProcessor, stock_name: str, start_date: str, end_date: str) -> str:
    """
    使用 StockAnalyzer 来对特定股票进行分析，并返回分析报告。
    你需要自己在 StockAnalyzer 中实现相应的逻辑。
    """
    analyzer = StockAnalyzer(processor)
    result = analyzer.analyze_stock(stock_name=stock_name, start_date=start_date, end_date=end_date)
    analysis_result = analyzer.get_stock_report(result)
    
    # 这里先返回一个测试字符串，供演示
    # analysis_result = f"这是关于【{stock_name}】从 {start_date} 到 {end_date} 的简要分析示例。"
    return analysis_result


def init_chat_manager(processor: QueryProcessor, stock_report: str) -> ChatManager:
    """
    初始化 ChatManager，用于聊天问答。
    """
    return ChatManager(processor, stock_report=stock_report)


def display_chat_interface():
    """
    显示聊天界面并处理用户输入。
    该函数会读取和更新 st.session_state 中的 chat_manager。
    """
    # 创建一个容器来存放所有内容
    chat_container = st.container()
    
    # 在容器的顶部显示标题
    with chat_container:
        st.markdown("### 智能问答")

        # 如果没有 chat_history，则初始化
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []
            # 将可能存在的 system 消息放入历史
            if st.session_state.chat_manager and st.session_state.chat_manager.history:
                for msg in st.session_state.chat_manager.history:
                    if msg["role"] == "system":
                        st.session_state["chat_history"].append(msg)

        # 创建一个子容器来显示消息历史
        message_container = st.container()
        
        # 添加操作按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button("清空聊天历史", key="clear_history"):
                # 只保留 system 消息
                system_messages = [
                    msg for msg in st.session_state["chat_history"] 
                    if msg["role"] == "system"
                ]
                st.session_state["chat_history"] = system_messages
                st.session_state.chat_manager.clear_history()
                st.success("聊天历史已清空！")
                st.rerun()

        with col2:
            if st.button("结束聊天", key="end_chat"):
                st.session_state.chat_started = False
                st.session_state.chat_manager = None
                st.session_state["chat_history"] = []
                st.success("聊天已结束！")
                st.rerun()

        # 在底部添加输入框
        user_input = st.chat_input("请输入您的问题:")

        # 在消息容器中显示历史消息
        with message_container:
            for msg in st.session_state["chat_history"]:
                if msg["role"] == "system":
                    # system 消息不在前端直接展示
                    continue
                if msg["role"] == "user":
                    with st.chat_message("user", avatar="👤"):
                        st.markdown(msg["content"])
                else:  # assistant
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(msg["content"])

        if user_input:
            # 将用户输入存到 chat_history
            st.session_state["chat_history"].append({"role": "user", "content": user_input})

            # 立刻在页面上显示用户输入
            with message_container:
                with st.chat_message("user", avatar="👤"):
                    st.markdown(user_input)

                # 显示机器人回答（流式）
                with st.chat_message("assistant", avatar="🤖"):
                    response_placeholder = st.empty()
                    # 添加加载动画
                    with st.spinner("AI思考中..."):
                        full_response = ""
                        # 将用户输入和股票名称组合
                        enriched_input = f"关于股票【{stock_name}】的问题：{user_input}"
                        for response_chunk in st.session_state.chat_manager.process_message(enriched_input):
                            full_response += response_chunk
                            response_placeholder.markdown(full_response)

                        # 将完整回复加入历史
                        st.session_state["chat_history"].append({"role": "assistant", "content": full_response})


# ---- 2. 页面主逻辑 ----

st.title("📊 智能股票分析助手")

# 侧边栏配置
with st.sidebar:
    st.header("配置参数")

    # LLM模型选择
    chat_model = st.selectbox(
        "选择LLM模型",
        ["deepseek-chat", "glm-4-plus"],
        index=0
    )

# 使用两列布局
col1, col2 = st.columns([2, 1])

with col1:
    # 子标题：生成股票研报
    st.subheader("生成股票研报")

    # 输入部分
    stock_name = st.text_input("输入股票名称", value="贵州茅台")

    # 日期选择
    col_date1, col_date2 = st.columns(2)
    with col_date1:
        start_date = st.date_input(
            "调研开始日期",
            datetime.now() - timedelta(days=30)
        )
    with col_date2:
        end_date = st.date_input(
            "调研结束日期",
            datetime.now() - timedelta(days=1)
        )

    # 点击按钮开始分析
    if st.button("开始分析", type="primary"):
        with st.spinner("正在分析中...(可能需要几分钟)"):
            try:
                # 1. 初始化处理器
                processor = init_query_processor(chat_model)
                
                # 2. 调用分析函数
                analysis_result = analyze_stock_report(
                    processor=processor,
                    stock_name=stock_name,
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d")
                )
                
                # 3. 将结果存储到 session_state
                st.session_state.analysis_result = analysis_result

                # 4. 初始化聊天管理器
                st.session_state.chat_manager = init_chat_manager(processor, analysis_result)

                # 5. 标记聊天已开始
                st.session_state.chat_started = True

                # 分析完成后提示
                st.success("分析完成！")

            except Exception as e:
                st.error(f"分析过程中出现错误: {str(e)}")

    # 只要 session_state 有分析结果，就显示研报
    if "analysis_result" in st.session_state:
        st.markdown("### 分析报告")
        st.write(st.session_state.analysis_result)

    # 如果已经开始聊天，则在研报下方显示聊天界面
    if st.session_state.get("chat_started"):
        display_chat_interface()

with col2:
    # 使用说明
    st.subheader("使用说明")
    st.markdown("""
    1. 在左侧选择需要使用的LLM模型。
    2. 请输入股票名称、选择调研开始日期和结束日期。
    3. 点击 **开始分析** 按钮，等待分析结果。
    4. 分析完成后可在 **智能问答** 区域与大模型进行针对该研报的深入讨论。
    
    **注意事项：**
    - 股票名称请输入完整的名称。
    - 时间范围不宜过长，否则分析速度会变慢。
    - 分析过程可能需要一些时间，请耐心等待。
    - 本系统使用AI大模型进行分析，结果仅供参考，不构成投资建议。
    """)

# 页脚
# from streamlit_autorefresh import st_autorefresh

# # 在 Streamlit 脚本里的某处（例如页脚）添加这段逻辑：
# # 设置自动刷新（单位毫秒），比如每 5 秒刷新一次
# count = st_autorefresh(interval=5000, limit=None, key="footer_autorefresh")

# st.markdown("---")
# st.markdown("### 实时日志")

# # 用一个可折叠组件来显示日志内容
# with st.expander("查看 chat_logs.txt 日志"):
#     try:
#         with open("chat_logs.txt", "r", encoding="utf-8") as f:
#             logs = f.read()
#         # 这里可以自由选择用 st.text_area、st.code、st.markdown 等
#         st.text_area("日志内容", logs, height=200)
#     except FileNotFoundError:
#         st.info("暂时没有可显示的日志记录或文件未找到。")
st.markdown("---")
st.markdown("### 💡 提示")
st.info("本系统使用AI大模型进行分析，结果仅供参考，不构成投资建议。")