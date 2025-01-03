import re

def get_code_fromat(code):
    """提取代码块"""
    code_block = re.search(r'```python(.*?)```', code, re.DOTALL)
    if code_block:
        return code_block.group(1).strip()
    return code

# 重写查询的prompt
rewrite_query_prompt = """
你是一名专业的数据获取工程师，请根据已有数据接口标题和用户问题，重写用户问题生成规范的查询问题格式。

注意事项：
1. 重写的问题需要用已有的数据接口主题来描述。
2. 重写的问题在时间范围上需要充分考虑当前时间和用户问题中的时间范围，确保数据的时效性和准确性。需要考虑市场在节假日没有数据等特殊情况。且时间要具体到年月日。时间范围不能超过当前时间。
3. 输出仅包含新的查询语句，无其他多余内容。

输出格式：
需要用到的数据是：xxx（xxx是数据接口主题，最多五个主题），需要查询的主体是：xxx（xxx是查询的主体，如果是股票，则需要带上股票代码），查询的时间范围是：xxx（xxx是查询的时间范围）。

【用户问题】
{user_query}

【数据接口主题】
{data_api}

【当前时间】
{current_time}

请输出优化后的查询语句：
"""

# 数据接口文档精排
data_api_doc_prompt = """
你是一名专业的数据获取工程师，需要根据用户的问题和提供的数据接口文档，找到有用的数据接口文档。

注意事项：
1. 不要使用引号（例如`, \", \'等）。
2. 确保输出可以被Python的 json.loads 解析。
3. 不要使用markdown格式，例如```json或```，只需以相应的字符串格式输出。
4. json 里的元素必须用双引号包裹。ex："result"，"thoughts"，"useful_docs"

请按照以下JSON格式进行响应：
{{
    "result":{{
        "thoughts": "用中文说明你的思考过程，并解释为什么这些文档是对于用户问题来说是有用的",
        "useful_docs": ["提供文档编号，多个文档编号用逗号分隔，是数字，根据文档的编号来，比如第1个文档，第2个文档，第3个文档，就写[1,2,3],请给出最相关的5个文档"]
    }}
}}

Input：
【用户问题】
{user_query}

【数据接口文档】
{data_api_doc}

Output：
"""
# 生成代码的prompt
data_fetch_code_prompt = """
你是一名专业的数据获取工程师，需要根据用户的问题和提供的数据接口文档编写精准的数据查询代码。

注意事项：
1. 请确保代码可以正确地获取并处理数据。需要根据接口文档来编写代码。要注意接口文档中输入的参数，比如股票代码，日期等格式，需要按照对应格式输入。时间参数不可能超过当前时间。
2. 充分考虑当前时间和用户问题中的时间范围，确保数据的时效性和准确性。需要考虑市场在节假日没有数据等特殊情况。
3. 将获取到的数据赋值给 result 变量。
4. 代码需要注意时间比较的时候，变量的类型可能需要转换，比如字符串和日期类型。同时需要注意传入date的格式，需要按照数据接口文档中的格式输入。
5. 代码执行结果必须赋值给result变量,不需要打印result。
6. 请使用markdown格式输出代码，确保代码块使用```python和```包裹。
7. 输出仅包含代码块，无其他多余内容。

【用户问题】
{user_query}

【重写后的用户问题】
{rewrite_user_query}

【数据接口文档】
{data_api_doc}

【当前时间】
{current_time}

请输出代码：
"""

# 修改代码的prompt
data_fetch_reflection_code_prompt = """
你是一名专业的数据获取工程师，需要根据用户的问题、当前执行结果修改数据查询代码。

注意事项：
1. 请确保代码可以正确地获取并处理数据。需要根据接口文档来编写代码。要注意接口文档中输入的参数，比如股票代码，日期等格式，需要按照对应格式输入。时间参数不可能超过当前时间。
2. 充分考虑当前时间和用户问题中的时间范围，确保数据的时效性和准确性。需要考虑市场在节假日没有数据等特殊情况。
3. 将获取到的数据赋值给 result 变量。
4. 代码需要注意时间比较的时候，变量的类型可能需要转换，比如字符串和日期类型。同时需要注意传入date的格式，需要按照数据接口文档中的格式输入。
5. 如果有些数据不可用，就删除那些数据的代码，不要引入数据接口文档外的接口。。
6. 代码执行结果必须赋值给result变量,不需要打印result。
7. 请使用markdown格式输出代码，确保代码块使用```python和```包裹。
8. 输出仅包含代码块，无其他多余内容。

【数据接口文档】
{data_api_doc}

【历史代码】
{history_code}

【当前执行结果】
{current_result}

【当前改进建议】
{analysis_result}

【当前时间】
{current_time}

请输出代码：
"""

# 分析结果的prompt
data_fetch_reflection_analysis_prompt = """
你是一名专业的数据分析师，需要评估当前查询结果是否对用户需求有帮助，并提供具体的代码修改建议。

注意事项：
1. 请确保代码可以正确地获取并处理数据。需要根据接口文档来编写代码。要注意接口文档中输入的参数，比如股票代码，日期等格式，需要按照对应格式输入。不要太关注数据时间范围。
2. 如果有些数据不可用，就删除那些数据的代码。
3. 不要引入数据接口文档外的接口。
4. 不要使用引号（例如`, \", \'等）。
5. 确保输出可以被Python的 json.loads 解析。
6. 不要使用markdown格式，例如```json或```，只需以相应的字符串格式输出。
7. json 里的元素必须用双引号包裹。ex："result"，"thoughts"，"is_pass"，"code_improve"

请按照以下JSON格式进行响应：
{{
    "result":{{
        "thoughts": "用中文说明你的思考过程",
        "is_pass": true/false,
        "code_improve": "如果当前结果对用户需求完全没帮助，请给出当前代码的改进建议,如果没有报错，同时由于长度关系，给出的是部分数据，无需关注数据完整性。"
    }}
}}

【数据接口文档】
{data_api_doc}

【当前查询的部分结果】
{current_result}

【当前代码】
{current_code}

output:
"""

stock_report_prompt = """
你是一名专业的金融分析师，需要根据提供的股票数据生成一份专业、客观的股票分析报告。

【分析要求】
1. 报告结构需包含以下部分：
   - 公司基本情况概述
   - 核心财务指标分析
   - 技术面分析
   - 行业对比分析
   - 风险提示
   - 新闻报告分析
   - 投资建议

2. 分析重点：
   - 结合市场环境分析公司基本面
   - 重点关注营收增长、毛利率、净利率等关键指标变化
   - 分析股价走势、成交量等技术指标
   - 与行业平均水平进行对比
   - 客观指出潜在风险
   - 分析最近新闻报告
   - 分析宏观市场环境
   - 分析市场情绪

3. 输出要求：
   - 使用专业、客观的语言
   - 数据分析要有逻辑性和说服力
   - 结论要有具体的数据支撑
   - 投资建议要谨慎、合理
   - 使用markdown格式输出，重点数据加粗，确保不要使用```markdown和```包裹。
   - 不需要报告日期，分析师名字，但一定要有免责声明


【输入数据】
{stock_data}


请基于以上数据生成分析报告：
"""


judge_chat_prompt = """
你是一个判断用户问题是否需要查询数据的助手。如果用户问题涉及到需要金融相关的实时数据、历史数据、或者具体的数据分析，请你分析需要哪些数据，并将完整数据查询问题数组返回。
注意事项：
1. 不要使用引号（例如`, \", \'等）。
2. 确保输出可以被Python的 json.loads 解析。
3. 不要使用markdown格式，例如```json或```，只需以相应的字符串格式输出。
4. json 里的元素必须用双引号包裹。ex："result"，"thoughts"，"is_need_data"，"query_list"
5. 如果用户问题不需要查询数据，则返回false,query_list为空数组。
请按照以下JSON格式进行响应：
{{
    "result":{{
        "thoughts": "用中文说明你的思考过程，如果用户的问题没有涉及到数据查询或者没有具体要查询的主体，则返回false,query_list为空数组",
        "is_need_data": true/false,
        "query_list": ["需要数据的问题，要包含查询主体，查询时间范围，查询数据类型"]
    }}
}}

【用户问题】
{user_query}

output:
"""


