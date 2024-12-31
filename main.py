import os
import sys

# 添加项目根目录到 Python 路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import json
import asyncio

from pydantic import BaseModel

from typing import List, Optional
from dotenv import load_dotenv

# 导入现有的处理模块
from agent.query import QueryProcessor
from agent.stock_analysis import StockAnalyzer
from agent.chat_manager import ChatManager

# 加载环境变量
load_dotenv()

app = FastAPI(title="股票分析助手API")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React默认端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic模型
class StockAnalysisRequest(BaseModel):
    stock_name: str
    start_date: str
    end_date: str
    chat_model: str = "deepseek-chat"

class ChatRequest(BaseModel):
    message: str
    stock_name: str
    chat_model: str = "deepseek-chat"  # 默认使用 deepseek-chat
    chat_history: Optional[List[dict]] = []

# 全局变量存储处理器实例
processors = {}
chat_managers = {}

def init_query_processor(chat_model: str) -> QueryProcessor:
    """初始化查询处理器"""
    if chat_model == "glm-4-plus":
        llm_api_key = os.getenv("zhipu_api_key")
        llm_base_url = os.getenv("zhipu_base_url")
    else:  # deepseek-chat
        llm_api_key = os.getenv("deepseek_api_key")
        llm_base_url = os.getenv("deepseek_base_url")
    
    embedding_api_key = os.getenv("zhipu_api_key")
    embedding_base_url = os.getenv("zhipu_base_url")
    
    if not llm_api_key or not llm_base_url:
        raise HTTPException(status_code=500, detail="API配置缺失")
    
    return QueryProcessor(
        llm_api_key=llm_api_key,
        llm_base_url=llm_base_url,
        chat_model=chat_model,
        embedding_model_name="embedding-3",
        embedding_store_dir=".index_all_embedding_3",
        embedding_api_key=embedding_api_key,
        embedding_base_url=embedding_base_url
    )

def get_or_create_chat_manager(stock_name: str, chat_model: str) -> ChatManager:
    """获取或创建聊天管理器"""
    if chat_model not in processors:
        processors[chat_model] = init_query_processor(chat_model)
    
    manager_key = f"{stock_name}_{chat_model}"
    if manager_key not in chat_managers:
        chat_managers[manager_key] = ChatManager(processors[chat_model])
    
    return chat_managers[manager_key]

@app.post("/api/analyze")
async def analyze_stock(request: StockAnalysisRequest):
    """分析股票接口"""
    try:
        # 获取或创建处理器
        if request.chat_model not in processors:
            processors[request.chat_model] = init_query_processor(request.chat_model)
        
        processor = processors[request.chat_model]
        analyzer = StockAnalyzer(processor)
        
        # 执行分析
        result = analyzer.analyze_stock(
            stock_name=request.stock_name,
            start_date=request.start_date,
            end_date=request.end_date
        )
        analysis_result = analyzer.get_stock_report(result)
        
        return {"status": "success", "report": analysis_result}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """聊天接口 - SSE 流式输出"""
    async def event_generator():
        try:
            print(f"处理聊天请求: {request.message}")

            # 获取或创建聊天管理器
            chat_manager = get_or_create_chat_manager(request.stock_name, request.chat_model)
            
            # 构建增强的输入
            enriched_input = f"关于股票【{request.stock_name}】的问题：{request.message}"
            print(f"开始处理问题: {enriched_input}")
            
            try:
                print("开始收集回复片段")
                async for chunk in chat_manager.process_message_async(enriched_input, request.stock_name):
                    if chunk:
                        print(f"发送回复片段: {chunk[:50]}...")
                        yield {
                            "event": "message",
                            "data": json.dumps({
                                "content": chunk,
                                "type": "content"
                            })
                        }
                        await asyncio.sleep(0.01)  # 小延迟以确保流畅输出
                
                # 发送完成信号
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "type": "done"
                    })
                }
                
            except Exception as e:
                error_msg = f"生成回复时出错: {str(e)}"
                print(error_msg)
                print("错误堆栈:")
                import traceback
                traceback.print_exc()
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "error": str(e),
                        "type": "error"
                    })
                }
        
        except Exception as e:
            error_msg = f"聊天处理出错: {str(e)}"
            print(error_msg)
            print("错误堆栈:")
            import traceback
            traceback.print_exc()
            yield {
                "event": "message",
                "data": json.dumps({
                    "error": str(e),
                    "type": "error"
                })
            }

    return EventSourceResponse(event_generator())

@app.get("/api/models")
async def get_available_models():
    """获取可用的模型列表"""
    return {
        "models": [
            {"id": "deepseek-chat", "name": "Deepseek Chat"},
            {"id": "glm-4-plus", "name": "GLM-4 Plus"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 