from typing import List, Dict, Generator, Union
from .query import QueryProcessor

class ChatManager:
    def __init__(self, query_processor: QueryProcessor, stock_report: str = None):
        self.query_processor = query_processor
        self.history: List[Dict[str, str]] = []
        self.max_history = 10  # 最大历史记录数
        
        # 如果提供了stock_report，添加固定的system消息
        if stock_report:
            self.history.append({
                "role": "system",
                "content": f"你是一个专业的股票分析师，需要基于以下股票研报来回答用户问题：\n{stock_report}"
            })
        
    def add_message(self, role: str, content: str):
        """添加消息到历史记录"""
        self.history.append({"role": role, "content": content})
        
        # 保持历史记录在最大限制内，但保留system消息
        if len(self.history) > self.max_history:
            # 找到第一个非system消息的索引
            non_system_index = 0
            for i, msg in enumerate(self.history):
                if msg["role"] != "system":
                    non_system_index = i
                    break
            # 删除第一条非system消息
            self.history.pop(non_system_index)
            
    def get_messages(self) -> List[Dict[str, str]]:
        """获取当前的消息历史"""
        return self.history.copy()
    
    def clear_history(self):
        """清空历史记录，但保留system消息"""
        # 保留所有system消息
        self.history = [msg for msg in self.history if msg["role"] == "system"]
        
    def process_message(self, user_message: str) -> Generator[str, None, None]:
        """处理用户消息并返回流式响应"""
        # 添加用户消息到历史
        self.add_message("user", user_message)
        
        # 检查是否需要使用query
        need_query = self.query_processor.check_need_query(user_message)
        
        if need_query:
            # 如果需要查询数据，使用process_query处理
            try:
                query_result = self.query_processor.query(user_message,True,10)
                # 将查询结果添加到消息中
                messages = self.get_messages()
                messages.append({
                    "role": "assistant",
                    "content": f"我已经查询到相关数据，让我为您分析：\n{str(query_result)}"
                })
            except Exception as e:
                messages = self.get_messages()
                messages.append({
                    "role": "assistant",
                    "content": f"在查询数据时遇到了问题：{str(e)}"
                })
        else:
            messages = self.get_messages()
            
        # 使用流式输出生成最终响应
        response_stream = self.query_processor.stream_chat_llm(messages)
        
        # 收集完整响应用于保存到历史记录
        full_response = ""
        
        for chunk in response_stream:
            if hasattr(chunk.choices[0].delta, 'content'):
                content = chunk.choices[0].delta.content
                if content:
                    full_response += content
                    yield content
                    
        # 将助手的完整响应添加到历史记录
        self.add_message("assistant", full_response) 