from datetime import datetime
import json_repair
from llm.api.func_get_openai import OpenaiApi
from llamaindex.indexstore import IndexStore
from promptstore.prompt import write_code_prompt,get_code_fromat,rewrite_query_prompt,reflection_write_code_prompt,reflection_analysis_prompt

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
        print(rewrite_user_query)
        # 构建提示词
        prompt = write_code_prompt.format(
            user_query=user_query,
            rewrite_user_query=rewrite_user_query,
            data_api_doc=doc_api,
            current_time=current_time
        )
        print(prompt)
        
        # 获取LLM响应
        messages = [{
            "role": "user",
            "content": prompt
        }]
        result = self.model.chat_model(messages)
        # 提取代码
        code = get_code_fromat(result)
        print(code)
        
        # 执行代码
        context = {}
        compiled_code = compile(code, '<string>', 'exec')
        exec(compiled_code, context)
        
        data = context.get('result')
        # 返回结果
        return data

    def _get_result_structure(self, result):
        """
        获取结果的数据结构
        
        Args:
            result: 查询结果（可能是dict或list）
            
        Returns:
            str: 数据结构描述
        """
        if isinstance(result, dict):
            return f"数据结构为字典，包含以下字段：{', '.join(result.keys())}"
        elif isinstance(result, list):
            if not result:
                return "数据结构为空列表"
            sample = result[0] if result else None
            if isinstance(sample, dict):
                return f"数据结构为列表，每个元素为字典，包含以下字段：{', '.join(sample.keys())}"
            else:
                return f"数据结构为列表，元素类型为：{type(sample).__name__}"
        else:
            return f"数据类型为：{type(result).__name__}"

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

            # 生成新的查询语句
            rewrite_query = rewrite_query_prompt.format(
                user_query=user_query,
                data_api=self.titles,
                current_time=current_time
            )
            messages = [{"role": "user", "content": rewrite_query}]
            rewrite_user_query = self.model.chat_model(messages)
            
            # 初始化变量
            current_code = None
            current_result = None
            analysis_result = None
            iteration = 0
            last_result = None
            consecutive_same_result = 0
            
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
                print(f'prompt: {prompt}')
                print(f'result: {result}')
                
                # 执行代码
                try:
                    context = {}
                    compiled_code = compile(current_code, '<string>', 'exec')
                    exec(compiled_code, context)
                    current_result = context.get('result', {})  
                except Exception as e:
                    print(f"代码执行错误: {str(e)}")
                    current_result = {"error": str(e)}
                
                # 检查结果是否与上次相同
                if last_result == current_result:
                    consecutive_same_result += 1
                    if consecutive_same_result >= 2:
                        print("检测到连续两次相同结果，重新开始查询流程")
                        return None  # 触发重新执行整个流程
                else:
                    consecutive_same_result = 0
                
                last_result = current_result
                
                # 分析结果
                result_structure = self._get_result_structure(current_result)+'\n部分数据结果：'+str(current_result)[:1000]
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
                    return current_result
                else:
                    analysis_result = thoughts+code_improve
                    print(f'analysis_result: {analysis_result}')
                iteration += 1
            
            return current_result

        # 主循环，最多重试3次
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            result = _execute_reflection_cycle()
            if result is not None:
                return result
            retry_count += 1
            print(f"开始第 {retry_count + 1} 次重试...")
        
        print("达到最大重试次数，返回最后一次结果")
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