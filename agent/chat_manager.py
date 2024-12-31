from typing import List, Dict, Generator, Union, AsyncGenerator
from .query import QueryProcessor

class ChatManager:
    def __init__(self, query_processor: QueryProcessor):
        self.query_processor = query_processor
        self.history: List[Dict[str, str]] = []
        self.max_history = 10  # 最大历史记录数
            
    def add_message(self, role: str, content: str):
        """添加消息到历史记录"""
        self.history.append({"role": role, "content": content})
        
        # 保持历史记录在最大限制内
        if len(self.history) > self.max_history:
            self.history.pop(0)  # 移除最早的消息
            
    def get_messages(self) -> List[Dict[str, str]]:
        """获取当前的消息历史"""
        return self.history.copy()
    
    def clear_history(self):
        """清空历史记录"""
        self.history = []

    async def process_message_async(self, user_message: str, stock_name: str = None) -> AsyncGenerator[str, None]:
        """异步处理用户消息并返回流式响应"""
        # 添加用户消息到历史
        self.add_message("user", user_message)
        
        # 检查是否需要使用query
        need_query = self.query_processor.check_need_query(user_message)
        
        if need_query:
            # 如果需要查询数据，使用process_query处理
            try:
                query_result = self.query_processor.query(user_message, True, 10)
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