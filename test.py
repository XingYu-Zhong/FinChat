import asyncio
import os
from agent.chat_manager import ChatManager
from dotenv import load_dotenv
from llm.api.func_get_openai import OpenaiApi
from llamaindex.indexstore import IndexStore
from log_manager import SyncLogManager
from agent.query import QueryAgent
from agent.stock_analysis import StockAnalyzer

# 加载环境变量
load_dotenv()

# API配置
llm_api_key = os.getenv("deepseek_api_key")
llm_base_url = os.getenv("deepseek_base_url")
chat_model = "deepseek-chat"
# llm_api_key = os.getenv("zhipu_api_key")
# llm_base_url = os.getenv("zhipu_base_url")
# chat_model = 'glm-4-plus'
# chat_model = 'codegeex-4'
embedding_model_name = 'embedding-3'
embedding_store_dir = '.index_all_embedding_3'
embedding_api_key = os.getenv("zhipu_api_key")
embedding_base_url = os.getenv("zhipu_base_url")

# 初始化基础组件
model = OpenaiApi(
    api_key=llm_api_key,
    base_url=llm_base_url,
    model=chat_model
)

index = IndexStore(
    embedding_model_name=embedding_model_name,
    index_dir=embedding_store_dir,
    update_rag_doc=False,
    api_key=embedding_api_key,
    base_url=embedding_base_url
)

log_manager = SyncLogManager("chat_logs.txt")

# 初始化 QueryAgent（新版）
processor = QueryAgent(
    model=model,
    log_manager=log_manager,
    index=index
)

# 初始化 StockAnalyzer
analyzer = StockAnalyzer(processor)
result = analyzer.analyze_stock("000063","20241223","20241229")
report = analyzer.get_stock_report(result)
print(report)

# # 初始化 ChatManager
# chat_manager = ChatManager(processor)

# async def main():
#     # 处理用户消息
#     user_message = "上周中兴通讯走势如何"
#     print(f"处理用户消息: {user_message}")
#     async for response_chunk in chat_manager.process_message_async(user_message):
#         print(response_chunk, end="", flush=True)
#     print()  # 打印一个换行

# if __name__ == "__main__":
#     # 运行异步主函数
#     asyncio.run(main())


