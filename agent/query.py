from datetime import datetime
from .sweagent import DataFetchAgent
from promptstore.prompt import rewrite_query_prompt, data_api_doc_prompt, judge_chat_prompt
import os
import json_repair
import json
from typing import List, Dict, Any, AsyncGenerator
import aiohttp
from llm.api.func_get_openai import OpenaiApi
from llamaindex.indexstore import IndexStore
from log_manager import SyncLogManager

# 配置日志文件路径
LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chat_logs.txt")

class QueryAgent:
    def __init__(self, llm_api_key=None, llm_base_url=None, chat_model="glm-4-plus", 
                 embedding_model_name="embedding-2", embedding_store_dir=".index_all_embedding_2",
                 update_rag_doc=False, embedding_api_key=None, embedding_base_url=None,
                 model=None, log_manager=None, index=None):
        """
        初始化QueryAgent
        
        Args:
            llm_api_key: LLM API密钥
            llm_base_url: LLM API基础URL
            chat_model: 聊天模型名称
            embedding_model_name: 嵌入模型名称
            embedding_store_dir: 嵌入存储目录
            update_rag_doc: 是否更新RAG文档
            embedding_api_key: 嵌入API密钥
            embedding_base_url: 嵌入API基础URL
            model: LLM模型实例（新增）
            log_manager: 日志管理器实例（新增）
            index: 索引实例（新增）
        """
        if model and log_manager and index:
            # 新版本初始化
            self.model = model
            self.log_manager = log_manager
            self.index = index
            self.titles = "\n".join(index.get_titles())
            self.code_agent = DataFetchAgent(model, log_manager, index)
        else:
            # 旧版本初始化
            self.llm_api_key = llm_api_key
            self.llm_base_url = llm_base_url
            self.chat_model = chat_model
            self.embedding_model_name = embedding_model_name
            self.embedding_store_dir = embedding_store_dir
            self.update_rag_doc = update_rag_doc
            # 初始化索引
            self.index = IndexStore(
                embedding_model_name=embedding_model_name,
                index_dir=embedding_store_dir,
                update_rag_doc=update_rag_doc,
                api_key=embedding_api_key,
                base_url=embedding_base_url
            )
            self.titles = "\n".join(self.index.get_titles())
            # 初始化LLM模型
            self.model = OpenaiApi(
                api_key=llm_api_key,
                base_url=llm_base_url,
                model=chat_model
            )
            # 初始化日志管理器
            self.log_manager = SyncLogManager(LOG_FILE)
            # 初始化DataFetchAgent
            self.code_agent = DataFetchAgent(self.model, self.log_manager, self.index)
    def get_code_agent(self):
        return self.code_agent
    def _get_current_time(self):
        """获取当前时间字符串"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def query(self, user_query, max_iterations=5):
        """
        使用reflection机制处理用户查询
        
        Args:
            user_query: 用户查询字符串
            max_iterations: 最大迭代次数，默认3次
            
        Returns:
            dict: 查询结果
        """
        current_time = self._get_current_time()
        self.log_manager.append_log(f"agent 开始查询: {user_query} \n--------------------------------")
        

        # 生成新的查询语句
        prompt = rewrite_query_prompt.format(
            user_query=user_query,
            data_api=self.titles,
            current_time=current_time
        )
        messages = [{"role": "user", "content": prompt}]
        rewrite_user_query = self.model.chat_model(messages)
        self.log_manager.append_log(f"agent 生成新的查询语句:\n {rewrite_user_query} \n--------------------------------")

        # 搜索相关API文档
        search_results = self.index.search(rewrite_user_query,10)
        doc_api_list = search_results[:min(10, len(search_results))]
        doc_api = "\n".join([f"【第{i}个文档】{doc}" for i, doc in enumerate(doc_api_list)])
        # # 精排API文档
        # prompt = data_api_doc_prompt.format(
        #     user_query=user_query+'\n[新的查询语句]\n'+rewrite_user_query,
        #     data_api_doc=doc_api
        # )
        # messages = [{"role": "user", "content": prompt}]
        # doc_api_str = self.model.chat_model(messages)
        # doc_api_json = json_repair.loads(doc_api_str)
        # rerank_doc_api_list = doc_api_json['result']['useful_docs']
        # rerank_thoughts = doc_api_json['result']['thoughts']
        # # 根据精排的文档编号，获取对应的文档
        # rerank_doc_api = "\n".join([f"【第{i+1}个文档】{doc_api_list[int(doc_id)]}" for i, doc_id in enumerate(rerank_doc_api_list)])
        # self.log_manager.append_log(f"agent 正在查找相关数据文档. rerank_doc_api_list：{rerank_doc_api_list} \n 相关的思考: {rerank_thoughts} \n-------------------------------- \n 精排后的API文档: {rerank_doc_api} \n--------------------------------")

        # 使用DataFetchAgent生成和执行代码
        return self.code_agent.generate_and_execute_data_fetch_code(
            user_query=user_query,
            rewrite_query=rewrite_user_query,
            doc_api=doc_api,
            max_iterations=max_iterations
        )

    def chat_llm(self, messages):
        """流式输出聊天响应"""
        return self.model.chat_model(messages)
    
    def stream_chat_llm(self, messages):
        """流式输出聊天响应"""
        return self.model.stream_chat_model(messages)
    
    def check_need_query(self, user_query):
        """检查是否需要使用query获取数据"""
        prompt = judge_chat_prompt.format(
            user_query=user_query
        )
        messages = [{
            "role": "system",
            "content": "你是一个判断用户问题是否需要查询数据的助手。如果用户问题涉及到需要实时数据、历史数据、或者具体的数据分析，就需要使用query。"
        }, {
            "role": "user",
            "content": prompt
        }]
        result = self.chat_llm(messages)
        judge_result = json_repair.loads(result)
        is_need_data = judge_result['result']['is_need_data']
        query_list = judge_result['result']['query_list']
        return is_need_data, query_list

    async def chat_stream(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """
        流式生成聊天回复
        
        Args:
            messages: 对话消息列表
            
        Yields:
            生成的回复片段
        """
        try:
            # 构建请求数据
            data = {
                "model": self.chat_model,
                "messages": messages,
                "stream": True,
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            # 发送请求并处理流式响应
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.llm_base_url}{self.chat_api_path}",
                    headers=self.headers,
                    json=data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(f"API请求失败: {response.status} - {error_text}")
                    
                    # 处理流式响应
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line:
                            if line.startswith('data: '):
                                line = line[6:]  # 移除 "data: " 前缀
                            if line == '[DONE]':
                                break
                            try:
                                chunk_data = json.loads(line)
                                if chunk_data.get('choices') and chunk_data['choices'][0].get('delta'):
                                    content = chunk_data['choices'][0]['delta'].get('content', '')
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                print(f"无法解析JSON: {line}")
                                continue
                            
        except Exception as e:
            error_msg = f"生成回复时出错: {str(e)}"
            print(error_msg)
            raise RuntimeError(error_msg)

    async def chat_once(self, messages: List[Dict[str, str]]) -> str:
        """
        生成单次聊天回复
        
        Args:
            messages: 对话消息列表
            
        Returns:
            完整的回复内容
        """
        response = []
        try:
            async for chunk in self.chat_stream(messages):
                response.append(chunk)
            return "".join(response)
        except Exception as e:
            raise RuntimeError(f"生成回复时出错: {str(e)}")

    def save_chat_history(self, history: List[Dict[str, str]], filename: str = None):
        """
        保存聊天历史
        
        Args:
            history: 聊天历史记录
            filename: 保存的文件名，如果为None则使用时间戳
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chat_history_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存聊天历史失败: {e}")

    def load_chat_history(self, filename: str) -> List[Dict[str, str]]:
        """
        加载聊天历史
        
        Args:
            filename: 历史记录文件名
            
        Returns:
            聊天历史记录列表
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载聊天历史失败: {e}")
            return [] 