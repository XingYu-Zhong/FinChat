from typing import Dict, Any
from datetime import datetime
import json_repair
from promptstore.prompt import data_fetch_code_prompt, data_fetch_reflection_code_prompt, data_fetch_reflection_analysis_prompt, get_code_fromat

class DataFetchAgent:
    def __init__(self, model, log_manager, index):
        """
        初始化DataFetchAgent
        
        Args:
            model: LLM模型实例
            log_manager: 日志管理器实例
            index: 检索索引实例
        """
        self.model = model
        self.log_manager = log_manager
        self.index = index

    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _execute_code(self, code: str) -> Dict[str, Any]:
        """
        执行代码并返回结果
        
        Args:
            code: 要执行的代码字符串
            
        Returns:
            Dict: 执行结果
        """
        try:
            context = {}
            compiled_code = compile(code, '<string>', 'exec')
            exec(compiled_code, context)
            return context.get('result', {})
        except Exception as e:
            import traceback
            error_info = traceback.format_exc()
            self.log_manager.append_log(f"代码执行错误:\n{error_info}\n--------------------------------")
            return {"error": str(e)+"\n"+error_info}

    def generate_and_execute_data_fetch_code(self, 
                                user_query: str,
                                rewrite_query: str,
                                doc_api: str,
                                max_iterations: int = 3,
                                max_retries: int = 3) -> Dict[str, Any]:
        """
        生成并执行数据获取代码，支持反思和重试机制
        
        Args:
            user_query: 用户查询
            rewrite_query: 重写后的查询
            doc_api: API文档
            max_iterations: 最大迭代次数
            max_retries: 最大重试次数
            
        Returns:
            Dict: 执行结果
        """
        def _execute_reflection_cycle():
            self.log_manager.append_log(f"agent 开始执行数据获取代码")

            current_time = self._get_current_time()
            
            # 初始化变量
            current_code = None
            current_result = None
            analysis_result = None
            iteration = 0
            historical_results = []
            
            while iteration < max_iterations:
                # 生成代码
                if current_code is None:
                    prompt = data_fetch_code_prompt.format(
                        user_query=user_query,
                        rewrite_user_query=rewrite_query,
                        data_api_doc=doc_api,
                        current_time=current_time
                    )
                else:
                    prompt = data_fetch_reflection_code_prompt.format(
                        data_api_doc=doc_api,
                        history_code=current_code,
                        current_result=str(current_result)[:1000],
                        analysis_result=analysis_result,
                        current_time=current_time
                    )
                
                messages = [{"role": "user", "content": prompt}]
                result = self.model.chat_model(messages)
                current_code = get_code_fromat(result)
                self.log_manager.append_log(f"agent 第{iteration}次生成执行代码:\n {current_code} \n--------------------------------")
                
                # 执行代码
                current_result = self._execute_code(current_code)
                
                # 检查重复结果
                result_str = str(current_result)
                if result_str in [str(r) for r in historical_results]:
                    self.log_manager.append_log("agent 检测到重复结果，重新开始查询流程")
                    return None
                
                historical_results.append(current_result)
                
                # 分析结果
                analysis_prompt = data_fetch_reflection_analysis_prompt.format(
                    data_api_doc=doc_api,
                    user_query=rewrite_query,
                    current_result=str(current_result)[:1000],
                    current_code=current_code,
                    current_time=current_time
                )
                
                messages = [{"role": "user", "content": analysis_prompt}]
                analysis_response = self.model.chat_model(messages)
                analysis_result = json_repair.loads(analysis_response)['result']
                is_pass = analysis_result['is_pass']
                thoughts = analysis_result['thoughts']
                code_improve = analysis_result['code_improve']
                
                if is_pass:
                    self.log_manager.append_log("agent 判断数据满足需求，返回结果")
                    return current_result
                else:
                    analysis_result = thoughts + code_improve
                    self.log_manager.append_log(f"agent 分析结果并提出修改建议:\n {analysis_result} \n--------------------------------")
                iteration += 1
            
            # 达到最大迭代次数，返回最长结果
            max_len = max(len(str(result)) for result in historical_results)
            return [result for result in historical_results if len(str(result)) == max_len][0]

        # 主循环，支持重试
        retry_count = 0
        while retry_count < max_retries:
            result = _execute_reflection_cycle()
            if result is not None:
                return result
            retry_count += 1
            self.log_manager.append_log(f"agent 开始第 {retry_count + 1} 次重试...")
        
        self.log_manager.append_log("agent 达到最大重试次数，返回最后一次结果")
        return _execute_reflection_cycle()  # 最后一次尝试 