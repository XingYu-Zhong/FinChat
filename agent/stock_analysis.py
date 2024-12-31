from agent.query import QueryProcessor
from promptstore.prompt import stock_report_prompt
import traceback

class StockAnalyzer:
    def __init__(self, query_processor: QueryProcessor):
        """
        初始化股票分析器
        
        Args:
            query_processor: QueryProcessor实例，用于执行查询
        """
        self.query_processor = query_processor
    
    def analyze_stock(self, stock_name: str, start_date: str, end_date: str,reflection_nums=10) -> dict:
        """
        分析指定时间段内的股票信息
        
        Args:
            stock_name: 股票名称
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            dict: 包含公司概况、估值分析和股票走势分析的结果
        """
        try:
            print(f"开始分析股票: {stock_name}")
            
            # 1. 查询公司概况
            company_info_query = f"请提供{stock_name}的个股信息"
            print(f"执行查询: {company_info_query}")
            company_info = self.query_processor.query(company_info_query, is_reflection=True, max_iterations=reflection_nums)
            print(f"公司概况查询结果: {str(company_info)[:200]}...")

            # 2. 估值分析
            valuation_query = f"请分析{stock_name}在{start_date}到{end_date}期间的估值情况"
            print(f"执行查询: {valuation_query}")
            valuation_analysis = self.query_processor.query(valuation_query, is_reflection=True, max_iterations=reflection_nums)
            print(f"估值分析查询结果: {str(valuation_analysis)[:200]}...")

            # 3. 股票走势分析
            trend_query = f"请分析{stock_name}在{start_date}到{end_date}期间的股价走势"
            print(f"执行查询: {trend_query}")
            trend_analysis = self.query_processor.query(trend_query, is_reflection=True, max_iterations=reflection_nums)
            print(f"走势分析查询结果: {str(trend_analysis)[:200]}...")

            # 4. 整合新闻数据
            news_query = f"请提供{start_date}到{end_date}期间关于{stock_name}的新闻数据"
            print(f"执行查询: {news_query}")
            news_info = self.query_processor.query(news_query, is_reflection=True, max_iterations=reflection_nums)
            print(f"新闻数据查询结果: {str(news_info)[:200]}...")

            # 5. 当前市场环境数据
            market_query = f"请提供{start_date}到{end_date}期间宏观环境数据"
            print(f"执行查询: {market_query}")
            market_info = self.query_processor.query(market_query, is_reflection=True, max_iterations=reflection_nums)
            print(f"市场环境查询结果: {str(market_info)[:200]}...")

            # 整合所有分析结果
            result = {
                "stock_name": stock_name,
                "analysis_period": {
                    "start_date": start_date,
                    "end_date": end_date
                },
                "company_profile": {
                    "query": company_info_query,
                    "result": company_info
                },
                "valuation_analysis": {
                    "query": valuation_query,
                    "result": valuation_analysis
                },
                "trend_analysis": {
                    "query": trend_query,
                    "result": trend_analysis
                },
                "news_reports": {
                    "query": news_query,
                    "result": news_info
                },
                "market_info": {
                    "query": market_query,
                    "result": market_info
                }
            }
            print("分析完成，返回结果")
            return result
            
        except Exception as e:
            print(f"分析过程中出现错误: {str(e)}")
            print("错误堆栈:")
            traceback.print_exc()
            raise Exception(f"股票分析失败: {str(e)}\n{traceback.format_exc()}")

    def get_stock_report(self, analysis_result: dict) -> str:
        """处理分析结果，生成报告"""
        try:
            print("开始生成股票报告")
            analysis_text = ''
            stock_name = analysis_result['stock_name']
            analysis_period = analysis_result['analysis_period']
            company_profile = analysis_result['company_profile']
            valuation_analysis = analysis_result['valuation_analysis']
            trend_analysis = analysis_result['trend_analysis']
            news_reports = analysis_result['news_reports']
            market_info = analysis_result['market_info']
            
            analysis_text += f"股票名称: {stock_name}\n"
            analysis_text += f"分析时间段: {analysis_period['start_date']} 到 {analysis_period['end_date']}\n"
            analysis_text += f"公司概况数据: {company_profile['result']}\n"
            analysis_text += f"估值分析数据: {valuation_analysis['result']}\n"
            analysis_text += f"股票走势分析数据: {trend_analysis['result']}\n"
            analysis_text += f"新闻报告数据: {news_reports['result']}\n"
            analysis_text += f"宏观市场环境数据: {market_info['result']}\n"

            print("生成报告提示词")
            report_prompt = stock_report_prompt.format(stock_data=analysis_text)
            messages = [
                {"role": "system", "content": "你是一名专业的金融分析师，需要根据提供的股票数据生成一份专业、客观的股票分析报告。"},
                {"role": "user", "content": report_prompt}
            ]
            print("调用LLM生成报告")
            report_result = self.query_processor.chat_llm(messages)
            print("报告生成完成")
            return report_result
            
        except Exception as e:
            print(f"生成报告时出现错误: {str(e)}")
            print("错误堆栈:")
            traceback.print_exc()
            raise Exception(f"生成股票报告失败: {str(e)}\n{traceback.format_exc()}")