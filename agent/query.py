from datetime import datetime
import os
import json_repair

import json
from typing import List, Dict, Any, AsyncGenerator
import aiohttp
from datetime import datetime
from llm.api.func_get_openai import OpenaiApi
from llamaindex.indexstore import IndexStore
from promptstore.prompt import write_code_prompt,get_code_fromat,rewrite_query_prompt,reflection_write_code_prompt,reflection_analysis_prompt
from log_manager import SyncLogManager
# 配置日志文件路径
LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chat_logs.txt")
class QueryProcessor:
    def __init__(self, llm_api_key, llm_base_url, chat_model="glm-4-plus", 
                 embedding_model_name="embedding-2", embedding_store_dir=".index_all_embedding_2",update_rag_doc=False,embedding_api_key=None,embedding_base_url=None):
        """
        初始化查询处理器
        
        Args:
            llm_api_key: LLM API密钥
            llm_base_url: LLM API基础URL
            chat_model: 聊天模型名称
            embedding_model_name: 嵌入模型名称
            embedding_store_dir: 嵌入存储目录
        """
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
        self.titles = self.index.get_titles()
        # 初始化LLM模型
        self.model = OpenaiApi(
            api_key=llm_api_key,
            base_url=llm_base_url,
            model=chat_model
        )
        # 初始化日志管理器
        self.log_manager = SyncLogManager(LOG_FILE)
    
    def chat_llm(self,messages):
        return self.model.chat_model(messages)
    
    def stream_chat_llm(self, messages):
        """流式输出聊天响应"""
        return self.model.stream_chat_model(messages)
    
    def check_need_query(self, user_query):
        """检查是否需要使用query获取数据"""
        messages = [{
            "role": "system",
            "content": "你是一个判断用户问题是否需要查询数据的助手。如果用户问题涉及到需要实时数据、历史数据、或者具体的数据分析，就需要使用query。"
        }, {
            "role": "user",
            "content": f"请判断这个问题是否需要使用query获取数据来回答：{user_query}\n只需要回答'是'或'否'。"
        }]
        result = self.chat_llm(messages)
        return "是" in result
    
    def _get_current_time(self):
        """获取当前时间和星期"""
        now = datetime.now()
        weekday = now.weekday()
        weekday_dict = {
            0: "星期一",
            1: "星期二", 
            2: "星期三",
            3: "星期四",
            4: "星期五",
            5: "星期六",
            6: "星期日"
        }
        current_weekday = weekday_dict[weekday]
        return str(now) + current_weekday

    def process_query(self, user_query):
        """
        处理用户查询
        
        Args:
            user_query: 用户查询字符串
            
        Returns:
            dict: 查询结果
        """
        # 获取当前时间
        current_time = self._get_current_time()
        
        # 搜索相关API文档
        search_results = self.index.search(user_query)
        doc_api_list = search_results[:min(5, len(search_results))]
        doc_api = "\n".join(doc_api_list)
        self.log_manager.append_log(f"agent 查找相关数据文档")
        # 生成新的查询语句
        rewrite_query = rewrite_query_prompt.format(
            user_query=user_query,
            data_api=self.titles,
            current_time=current_time
        )
        # 获取LLM响应
        messages = [{
            "role": "user",
            "content": rewrite_query
        }]
        rewrite_user_query = self.model.chat_model(messages)
        self.log_manager.append_log(f"agent 生成新的查询语句:\n {rewrite_user_query} \n--------------------------------")
        # 构建提示词
        prompt = write_code_prompt.format(
            user_query=user_query,
            rewrite_user_query=rewrite_user_query,
            data_api_doc=doc_api,
            current_time=current_time
        )
     
        
        # 获取LLM响应
        messages = [{
            "role": "user",
            "content": prompt
        }]
        result = self.model.chat_model(messages)
        # 提取代码
        code = get_code_fromat(result)
        self.log_manager.append_log(f"agent 生成执行代码:\n {code} \n--------------------------------")
        
        # 执行代码
        context = {}
        compiled_code = compile(code, '<string>', 'exec')
        exec(compiled_code, context)
        
        data = context.get('result')
        self.log_manager.append_log(f"agent 执行代码结果:\n {data} \n--------------------------------")
        # 返回结果
        return data


    def _check_analysis_result(self, analysis_result):
        """
        检查分析结果是否表明当前结果满足需求
        
        Args:
            analysis_result: LLM的分析结果
            
        Returns:
            bool: 是否满足需求
        """
        if not analysis_result:
            return False
            
        # 分析结果的第一行应该是"是"或"否"
        first_line = analysis_result.strip().split('\n')[0].strip()
        return first_line == "1. 是" or first_line == "是"

    def process_query_with_reflection(self, user_query, max_iterations=3):
        """
        使用reflection机制处理用户查询
        
        Args:
            user_query: 用户查询字符串
            max_iterations: 最大迭代次数，默认3次
            
        Returns:
            dict: 查询结果
        """
        def _execute_reflection_cycle():
            current_time = self._get_current_time()
            
            # 搜索相关API文档
            search_results = self.index.search(user_query)
            doc_api_list = search_results[:min(5, len(search_results))]
            doc_api = "\n".join(doc_api_list)
            self.log_manager.append_log(f"agent 正在查找相关数据文档")
            # 生成新的查询语句
            rewrite_query = rewrite_query_prompt.format(
                user_query=user_query,
                data_api=self.titles,
                current_time=current_time
            )
            messages = [{"role": "user", "content": rewrite_query}]
            rewrite_user_query = self.model.chat_model(messages)
            self.log_manager.append_log(f"agent 生成新的查询语句:\n {rewrite_user_query} \n--------------------------------")
            
            # 初始化变量
            current_code = None
            current_result = None
            analysis_result = None
            iteration = 0
            historical_results = []  # 改用列表存储历史结果
            
            while iteration < max_iterations:
                # 第一次执行或需要修改代码
                if current_code is None:
                    prompt = write_code_prompt.format(
                        user_query=user_query,
                        rewrite_user_query=rewrite_user_query,
                        data_api_doc=doc_api,
                        current_time=current_time
                    )
                else:
                    prompt = reflection_write_code_prompt.format(
                        data_api_doc=doc_api,
                        current_result=str(current_result)[:1000],
                        analysis_result=analysis_result,
                        history_code=current_code
                    )
                
                messages = [{"role": "user", "content": prompt}]
                result = self.model.chat_model(messages)
                current_code = get_code_fromat(result)
                self.log_manager.append_log(f"agent 第{iteration}次生成执行代码:\n {current_code} \n--------------------------------")
                
                # 执行代码
                try:
                    context = {}
                    compiled_code = compile(current_code, '<string>', 'exec')
                    exec(compiled_code, context)
                    current_result = context.get('result', {})  
                except Exception as e:
                    self.log_manager.append_log(f"agent 代码执行错误:\n {str(e)} \n--------------------------------")
                    current_result = {"error": str(e)}
                
                # 将当前结果添加到历史列表
                result_str = str(current_result)  # 转换为字符串用于比较
                if result_str in [str(r) for r in historical_results]:
                    self.log_manager.append_log("agent 检测到重复结果，重新开始查询流程")
                    return None
                
                historical_results.append(current_result)
                
                # 分析结果
                result_structure = '\n部分数据结果：'+str(current_result)[:1000]
                analysis_prompt = reflection_analysis_prompt.format(
                    user_query=user_query,
                    data_api_doc=doc_api,
                    current_result=result_structure,
                    current_code=current_code
                )
                messages = [{"role": "user", "content": analysis_prompt}]
                analysis_result = self.model.chat_model(messages)
                analysis_result = json_repair.loads(analysis_result)['result']
                is_pass = analysis_result['is_pass']
                thoughts = analysis_result['thoughts']
                code_improve = analysis_result['code_improve']
                
                # 如果结果满足需求，返回结果
                if is_pass:
                    self.log_manager.append_log("agent 判断数据满足需求，返回结果")
                    return current_result
                else:
                    analysis_result = thoughts+code_improve
                    self.log_manager.append_log(f"agent 分析结果并提出修改建议:\n {analysis_result} \n--------------------------------")
                iteration += 1
            
            # 如果达到最大迭代次数，返回元素里len最大的结果
            max_len = max(len(result) for result in historical_results)
            return [result for result in historical_results if len(result) == max_len][0]

        # 主循环，最多重试3次
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            result = _execute_reflection_cycle()
            if result is not None:
                return result
            retry_count += 1
            self.log_manager.append_log(f"agent 开始第 {retry_count + 1} 次重试...")
        
        self.log_manager.append_log("agent 达到最大重试次数，返回最后一次结果")
        return _execute_reflection_cycle()  # 最后一次尝试，无论结果如何都返回
    
    def query(self, user_query, is_reflection=False, max_iterations=3):
        """
        统一的查询接口，可以选择使用普通查询或带反思机制的查询
        
        Args:
            user_query: 用户查询字符串
            is_reflection: 是否使用反思机制，默认为False
            max_iterations: 反思机制的最大迭代次数，默认3次
            
        Returns:
            dict: 查询结果
        """
        if is_reflection:
            return self.process_query_with_reflection(user_query, max_iterations)
        else:
            return self.process_query(user_query)
        
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