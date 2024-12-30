
import os
from dotenv import load_dotenv
load_dotenv()
from agent.query import QueryProcessor
from agent.stock_analysis import StockAnalyzer
# llm_api_key = os.getenv("deepseek_api_key")
# llm_base_url = os.getenv("deepseek_base_url")
# chat_model = "deepseek-chat"
llm_api_key = os.getenv("zhipu_api_key")
llm_base_url = os.getenv("zhipu_base_url")
chat_model = 'glm-4-plus'
# chat_model = 'codegeex-4'
embedding_model_name = 'embedding-3'
embedding_store_dir = '.index_all_embedding_3'
embedding_api_key = os.getenv("zhipu_api_key")
embedding_base_url = os.getenv("zhipu_base_url")
#用户问题
user_query = "获取最近中兴通讯表现如何"


# 初始化
processor = QueryProcessor(
    llm_api_key=llm_api_key,
    llm_base_url=llm_base_url,
    chat_model=chat_model,
    embedding_model_name=embedding_model_name,
    embedding_store_dir=embedding_store_dir,
    embedding_api_key=embedding_api_key,
    # update_rag_doc=True,
    embedding_base_url=embedding_base_url
)


# 初始化 StockAnalyzer
analyzer = StockAnalyzer(processor)

# 分析股票
result = analyzer.analyze_stock(
    stock_name="贵州茅台",
    start_date="2024-11-01",
    end_date="2024-12-01"
)


# result = 
analysis_result = analyzer.get_stock_report(result)
print(analysis_result)


