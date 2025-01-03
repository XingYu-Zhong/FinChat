from agent.query import QueryAgent
from promptstore.prompt import stock_report_prompt
import traceback

class StockAnalyzer:
    def __init__(self, query_processor: QueryAgent):
        """
        初始化股票分析器
        
        Args:
            query_processor: QueryProcessor实例，用于执行查询
        """
        self.query_processor = query_processor
        self.code_agent = query_processor.get_code_agent()
    
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
            doc_api = """
#### 个股信息查询

接口: stock_individual_info_em

目标地址: http://quote.eastmoney.com/concept/sh603777.html?from=classic

描述: 东方财富-个股-股票信息

限量: 单次返回指定 symbol 的个股信息

输入参数

| 名称      | 类型    | 描述                      |
|---------|-------|-------------------------|
| symbol  | str   | symbol="603777"; 股票代码   |
| timeout | float | timeout=None; 默认不设置超时参数 |

输出参数

| 名称    | 类型     | 描述  |
|-------|--------|-----|
| item  | object | -   |
| value | object | -   |

接口示例

```python
import akshare as ak

stock_individual_info_em_df = ak.stock_individual_info_em(symbol="000001")
print(stock_individual_info_em_df)
```

数据示例

```
   item                value
0   总市值  337468917463.220032
1  流通市值      337466070320.25
2    行业                   银行
3  上市时间             19910403
4  股票代码               000001
5  股票简称                 平安银行
6   总股本        19405918198.0
7   流通股        19405754475.0
```
##### 机构参与度

接口: stock_comment_detail_zlkp_jgcyd_em

目标地址: https://data.eastmoney.com/stockcomment/stock/600000.html

描述: 东方财富网-数据中心-特色数据-千股千评-主力控盘-机构参与度

限量: 单次获取所有 symbol 的数据

输入参数

| 名称     | 类型  | 描述              |
|--------|-----|-----------------|
| symbol | str | symbol="600000" |

输出参数

| 名称    | 类型      | 描述      |
|-------|---------|---------|
| 交易日   | object  | -       |
| 机构参与度 | float64 | 注意单位: % |

接口示例

```python
import akshare as ak

stock_comment_detail_zlkp_jgcyd_em_df = ak.stock_comment_detail_zlkp_jgcyd_em(symbol="600000")
print(stock_comment_detail_zlkp_jgcyd_em_df)
```

数据示例

```
         交易日  机构参与度
0   2024-07-25  28.90860
1   2024-07-26  30.96772
2   2024-07-29  33.18196
3   2024-07-30  29.74948
4   2024-07-31  26.50768
5   2024-08-01  31.43596
6   2024-08-02  30.74792
7   2024-08-05  30.00552
8   2024-08-06  28.46816
9   2024-08-07  27.28048
10  2024-08-08  25.62168
11  2024-08-09  28.76180
12  2024-08-12  22.34396
13  2024-08-13  25.12816
14  2024-08-14  19.10376
15  2024-08-15  26.32104
16  2024-08-16  27.09764
17  2024-08-19  33.85404
18  2024-08-20  26.12312
19  2024-08-21  24.80908
20  2024-08-22  23.36916
21  2024-08-23  27.57504
22  2024-08-26  29.63956
23  2024-08-27  23.29028
24  2024-08-28  20.18936
25  2024-08-29  24.87316
26  2024-08-30  24.68128
27  2024-09-02  25.37456
28  2024-09-03  27.86884
29  2024-09-04  25.54656
30  2024-09-05  22.02124
31  2024-09-06  19.94916
32  2024-09-09  17.86148
33  2024-09-10  34.34128
34  2024-09-11  24.62652
35  2024-09-12  34.83748
36  2024-09-13  24.70888
37  2024-09-18  26.05112
38  2024-09-19  24.63440
39  2024-09-20  18.15912
40  2024-09-23  24.80804
41  2024-09-24  30.84384
```
#### 综合评价

##### 历史评分

接口: stock_comment_detail_zhpj_lspf_em

目标地址: https://data.eastmoney.com/stockcomment/stock/600000.html

描述: 东方财富网-数据中心-特色数据-千股千评-综合评价-历史评分

限量: 单次获取指定 symbol 的数据

输入参数

| 名称     | 类型  | 描述              |
|--------|-----|-----------------|
| symbol | str | symbol="600000" |

输出参数

| 名称  | 类型      | 描述  |
|-----|---------|-----|
| 日期  | object  | -   |
| 评分  | float64 | -   |

接口示例

```python
import akshare as ak

stock_comment_detail_zhpj_lspf_em_df = ak.stock_comment_detail_zhpj_lspf_em(symbol="600000")
print(stock_comment_detail_zhpj_lspf_em_df)
```

数据示例

```
      交易日         评分
0   2024-08-13  62.512173
1   2024-08-14  61.670775
2   2024-08-15  63.852884
3   2024-08-16  63.075082
4   2024-08-19  68.835333
5   2024-08-20  64.755213
6   2024-08-21  64.289915
7   2024-08-22  64.394597
8   2024-08-23  61.212378
9   2024-08-26  63.819157
10  2024-08-27  62.614203
11  2024-08-28  63.118215
12  2024-08-29  60.579603
13  2024-08-30  62.166671
14  2024-09-02  66.166225
15  2024-09-03  61.715196
16  2024-09-04  61.016823
17  2024-09-05  60.898236
18  2024-09-06  59.813002
19  2024-09-09  60.014454
20  2024-09-10  64.019089
21  2024-09-11  59.987986
22  2024-09-12  62.374324
23  2024-09-13  63.184084
24  2024-09-18  62.877090
25  2024-09-19  62.136208
26  2024-09-20  59.141378
27  2024-09-23  60.765932
28  2024-09-24  67.036800
29  2024-09-25  73.137028
```

#### 市场热度

##### 用户关注指数

接口: stock_comment_detail_scrd_focus_em

目标地址: https://data.eastmoney.com/stockcomment/stock/600000.html

描述: 东方财富网-数据中心-特色数据-千股千评-市场热度-用户关注指数

限量: 单次获取所有数据

输入参数

| 名称     | 类型  | 描述              |
|--------|-----|-----------------|
| symbol | str | symbol="600000" |

输出参数

| 名称     | 类型      | 描述 |
|--------|---------|----|
| 交易日    | object  | -  |
| 用户关注指数 | float64 | -  |

接口示例

```python
import akshare as ak

stock_comment_detail_scrd_focus_em_df = ak.stock_comment_detail_scrd_focus_em(symbol="600000")
print(stock_comment_detail_scrd_focus_em_df)
```

数据示例

```
       交易日  用户关注指数
0   2024-08-15    91.2
1   2024-08-16    91.6
2   2024-08-19    92.4
3   2024-08-20    92.4
4   2024-08-21    92.0
5   2024-08-22    92.0
6   2024-08-23    92.4
7   2024-08-26    92.4
8   2024-08-27    91.6
9   2024-08-28    92.0
10  2024-08-29    92.0
11  2024-08-30    91.2
12  2024-09-02    91.2
13  2024-09-03    91.2
14  2024-09-04    91.2
15  2024-09-05    91.2
16  2024-09-06    91.2
17  2024-09-09    92.4
18  2024-09-10    92.0
19  2024-09-11    91.6
20  2024-09-12    91.6
21  2024-09-13    93.2
22  2024-09-18    93.2
23  2024-09-19    92.8
24  2024-09-20    92.4
25  2024-09-23    92.8
26  2024-09-24    93.2
27  2024-09-25    93.2
28  2024-09-26    93.2
29  2024-09-27    92.4
```

##### 市场参与意愿

接口: stock_comment_detail_scrd_desire_em

目标地址: https://data.eastmoney.com/stockcomment/stock/600000.html

描述: 东方财富网-数据中心-特色数据-千股千评-市场热度-市场参与意愿

限量: 单次获取所有数据

输入参数

| 名称     | 类型  | 描述              |
|--------|-----|-----------------|
| symbol | str | symbol="600000" |

输出参数

| 名称   | 类型         | 描述  |
|------|------------|-----|
| 日期时间 | datetime64 | -   |
| 大户   | float64    | -   |
| 全部   | float64    | -   |
| 散户   | float64    | -   |

接口示例

```python
import akshare as ak

stock_comment_detail_scrd_desire_em_df = ak.stock_comment_detail_scrd_desire_em(symbol="600000")
print(stock_comment_detail_scrd_desire_em_df)
```

数据示例

```
                  日期时间    大户    全部    散户
0  2022-04-22 09:30:00  0.24  0.00 -0.25
1  2022-04-22 09:40:00  0.20 -0.04 -0.29
2  2022-04-22 09:50:00  0.16 -0.08 -0.33
3  2022-04-22 10:00:00  0.08 -0.10 -0.29
4  2022-04-22 10:10:00  0.00 -0.16 -0.33
5  2022-04-22 10:20:00  0.00 -0.16 -0.33
6  2022-04-22 10:30:00  0.00 -0.16 -0.33
7  2022-04-22 10:40:00  0.00 -0.14 -0.29
8  2022-04-22 10:50:00  0.04 -0.08 -0.20
9  2022-04-22 11:00:00  0.08 -0.06 -0.20
10 2022-04-22 11:10:00  0.12 -0.08 -0.29
11 2022-04-22 11:20:00  0.08 -0.14 -0.37
12 2022-04-22 11:30:00  0.12 -0.12 -0.37
13 2022-04-22 13:00:00  0.04 -0.12 -0.29
14 2022-04-22 13:10:00  0.00 -0.16 -0.33
15 2022-04-22 13:20:00  0.04 -0.14 -0.33
16 2022-04-22 13:30:00  0.00 -0.16 -0.33
17 2022-04-22 13:40:00  0.00 -0.18 -0.37
18 2022-04-22 13:50:00 -0.04 -0.20 -0.37
19 2022-04-22 14:00:00 -0.04 -0.20 -0.37
20 2022-04-22 14:10:00  0.00 -0.18 -0.37
21 2022-04-22 14:20:00  0.08 -0.16 -0.41
22 2022-04-22 14:30:00  0.04 -0.20 -0.45
23 2022-04-22 14:40:00 -0.04 -0.26 -0.49
24 2022-04-22 14:50:00 -0.12 -0.30 -0.49
25 2022-04-22 15:00:00 -0.12 -0.26 -0.41
```

##### 日度市场参与意愿

接口: stock_comment_detail_scrd_desire_daily_em

目标地址: https://data.eastmoney.com/stockcomment/stock/600000.html

描述: 东方财富网-数据中心-特色数据-千股千评-市场热度-日度市场参与意愿

限量: 单次获取指定 symbol 的数据

输入参数

| 名称     | 类型  | 描述              |
|--------|-----|-----------------|
| symbol | str | symbol="600000" |

输出参数

| 名称         | 类型      | 描述 |
|------------|---------|----|
| 交易日        | object  | -  |
| 当日意愿上升     | float64 | -  |
| 5日平均参与意愿变化 | float64 | -  |

接口示例

```python
import akshare as ak

stock_comment_detail_scrd_desire_daily_em_df = ak.stock_comment_detail_scrd_desire_daily_em(symbol="600000")
print(stock_comment_detail_scrd_desire_daily_em_df)
```

数据示例

```
     交易日  当日意愿上升  5日平均参与意愿变化
0  2024-09-18    4.76        1.00
1  2024-09-19    7.57        2.19
2  2024-09-20  -10.55        1.00
3  2024-09-23    8.85        1.00
4  2024-09-24    7.42        3.61
```

##### 市场成本

接口: stock_comment_detail_scrd_cost_em

目标地址: https://data.eastmoney.com/stockcomment/stock/600000.html

描述: 东方财富网-数据中心-特色数据-千股千评-市场热度-市场成本

限量: 单次获取所有数据

输入参数

| 名称     | 类型  | 描述              |
|--------|-----|-----------------|
| symbol | str | symbol="600000" |

输出参数

| 名称     | 类型      | 描述  |
|--------|---------|-----|
| 日期     | object  | -   |
| 市场成本   | float64 | -   |
| 5日市场成本 | float64 | -   |

接口示例

```python
import akshare as ak

stock_comment_detail_scrd_cost_em_df = ak.stock_comment_detail_scrd_cost_em(symbol="600000")
print(stock_comment_detail_scrd_cost_em_df)
```

数据示例

```
        日期  市场成本  5日市场成本
0  2022-04-18  8.05    8.09
1  2022-04-19  8.07    8.09
2  2022-04-20  8.11    8.09
3  2022-04-21  8.06    8.08
4  2022-04-22  8.08    8.07
```

            """
            company_info_query = f"请提供{stock_name}的个股信息"
            company_info = self.code_agent.generate_and_execute_data_fetch_code(
                user_query=company_info_query,
                rewrite_query=company_info_query,
                doc_api=doc_api,
                max_iterations=reflection_nums
            )

            # 3. 股票走势分析
            trend_query = f"请分析{stock_name}在{start_date}到{end_date}期间的历史股价走势"
            doc_api = """
            ##### 历史行情数据-东财

接口: stock_zh_a_hist

目标地址: https://quote.eastmoney.com/concept/sh603777.html?from=classic(示例)

描述: 东方财富-沪深京 A 股日频率数据; 历史数据按日频率更新, 当日收盘价请在收盘后获取

限量: 单次返回指定沪深京 A 股上市公司、指定周期和指定日期间的历史行情日频率数据

输入参数

| 名称         | 类型    | 描述                                                       |
|------------|-------|----------------------------------------------------------|
| symbol     | str   | symbol='603777'; 股票代码可以在 **ak.stock_zh_a_spot_em()** 中获取 |
| period     | str   | period='daily'; choice of {'daily', 'weekly', 'monthly'} |
| start_date | str   | start_date='20210301'; 开始查询的日期                           |
| end_date   | str   | end_date='20210616'; 结束查询的日期                             |
| adjust     | str   | 默认返回不复权的数据; qfq: 返回前复权后的数据; hfq: 返回后复权后的数据               |
| timeout    | float | timeout=None; 默认不设置超时参数                                  |

输出参数-历史行情数据

| 名称   | 类型      | 描述          |
|------|---------|-------------|
| 日期   | object  | 交易日         |
| 股票代码 | object  | 不带市场标识的股票代码 |
| 开盘   | float64 | 开盘价         |
| 收盘   | float64 | 收盘价         |
| 最高   | float64 | 最高价         |
| 最低   | float64 | 最低价         |
| 成交量  | int64   | 注意单位: 手     |
| 成交额  | float64 | 注意单位: 元     |
| 振幅   | float64 | 注意单位: %     |
| 涨跌幅  | float64 | 注意单位: %     |
| 涨跌额  | float64 | 注意单位: 元     |
| 换手率  | float64 | 注意单位: %     |

接口示例-历史行情数据-不复权

```python
import akshare as ak

stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20170301", end_date='20240528', adjust="")
print(stock_zh_a_hist_df)
```

数据示例-历史行情数据-不复权

```
            日期    股票代码   开盘   收盘  ... 振幅  涨跌幅  涨跌额 换手率
0     2017-03-01  000001   9.49   9.49  ...  0.84  0.11  0.01  0.21
1     2017-03-02  000001   9.51   9.43  ...  1.26 -0.63 -0.06  0.24
2     2017-03-03  000001   9.41   9.40  ...  0.74 -0.32 -0.03  0.20
3     2017-03-06  000001   9.40   9.45  ...  0.74  0.53  0.05  0.24
4     2017-03-07  000001   9.44   9.45  ...  0.63  0.00  0.00  0.17
...          ...     ...    ...    ...  ...   ...   ...   ...   ...
1755  2024-05-22  000001  11.56  11.56  ...  2.42  0.09  0.01  1.09
1756  2024-05-23  000001  11.53  11.40  ...  1.90 -1.38 -0.16  0.95
1757  2024-05-24  000001  11.37  11.31  ...  1.67 -0.79 -0.09  0.72
1758  2024-05-27  000001  11.31  11.51  ...  1.95  1.77  0.20  0.75
1759  2024-05-28  000001  11.50  11.40  ...  1.91 -0.96 -0.11  0.62
[1760 rows x 12 columns]
```

接口示例-历史行情数据-前复权

```python
import akshare as ak

stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20170301", end_date='20240528', adjust="qfq")
print(stock_zh_a_hist_df)
```

接口示例-历史行情数据-后复权

```python
import akshare as ak

stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20170301", end_date='20240528', adjust="hfq")
print(stock_zh_a_hist_df)
```

##### 历史行情数据-新浪

接口: stock_zh_a_daily

P.S. 建议切换为 stock_zh_a_hist 接口使用(该接口数据质量高, 访问无限制)

目标地址: https://finance.sina.com.cn/realstock/company/sh600006/nc.shtml(示例)

描述: 新浪财经-沪深京 A 股的数据, 历史数据按日频率更新; 注意其中的 **sh689009** 为 CDR, 请 通过 **ak.stock_zh_a_cdr_daily** 接口获取

限量: 单次返回指定沪深京 A 股上市公司指定日期间的历史行情日频率数据, 多次获取容易封禁 IP

输入参数

| 名称         | 类型  | 描述                                                                                   |
|------------|-----|--------------------------------------------------------------------------------------|
| symbol     | str | symbol='sh600000'; 股票代码可以在 **ak.stock_zh_a_spot()** 中获取                              |
| start_date | str | start_date='20201103'; 开始查询的日期                                                       |
| end_date   | str | end_date='20201116'; 结束查询的日期                                                         |
| adjust     | str | 默认返回不复权的数据; qfq: 返回前复权后的数据; hfq: 返回后复权后的数据; hfq-factor: 返回后复权因子; qfq-factor: 返回前复权因子 |

输出参数-历史行情数据

| 名称                | 类型      | 描述            |
|-------------------|---------|---------------|
| date              | object  | 交易日           |
| open              | float64 | 开盘价           |
| high              | float64 | 最高价           |
| low               | float64 | 最低价           |
| close             | float64 | 收盘价           |
| volume            | float64 | 成交量; 注意单位: 股  |
| amount            | float64 | 成交额; 注意单位: 元  |
| outstanding_share | float64 | 流动股本; 注意单位: 股 |
| turnover          | float64 | 换手率=成交量/流动股本  |

接口示例-历史行情数据(前复权)

```python
import akshare as ak

stock_zh_a_daily_qfq_df = ak.stock_zh_a_daily(symbol="sz000001", start_date="19910403", end_date="20231027", adjust="qfq")
print(stock_zh_a_daily_qfq_df)
```

接口示例-历史行情数据(后复权)

```python
import akshare as ak

stock_zh_a_daily_hfq_df = ak.stock_zh_a_daily(symbol="sz000001", start_date="19910403", end_date="20231027", adjust="hfq")
print(stock_zh_a_daily_hfq_df)
```

            """
            trend_analysis = self.code_agent.generate_and_execute_data_fetch_code(
                user_query=trend_query,
                rewrite_query=trend_query,
                doc_api=doc_api,
                max_iterations=reflection_nums
            )


            # 4. 整合新闻数据
            news_query = f"请提供{start_date}到{end_date}期间关于{stock_name}的新闻数据"
            doc_api = """
            ### 个股新闻

接口: stock_news_em

目标地址: https://so.eastmoney.com/news/s

描述: 东方财富指定个股的新闻资讯数据

限量: 指定 symbol 当日最近 100 条新闻资讯数据

输入参数

| 名称     | 类型  | 描述                          |
|--------|-----|-----------------------------|
| symbol | str | symbol="300059"; 股票代码或其他关键词 |

输出参数

| 名称   | 类型     | 描述  |
|------|--------|-----|
| 关键词  | object | -   |
| 新闻标题 | object | -   |
| 新闻内容 | object | -   |
| 发布时间 | object | -   |
| 文章来源 | object | -   |
| 新闻链接 | object | -   |

接口示例

```python
import akshare as ak

stock_news_em_df = ak.stock_news_em(symbol="300059")
print(stock_news_em_df)
```

数据示例

```
       关键词  ...                                               新闻链接
0   300059  ...  http://finance.eastmoney.com/a/202405103073124...
1   300059  ...  http://finance.eastmoney.com/a/202405103073132...
2   300059  ...  http://finance.eastmoney.com/a/202404243057785...
3   300059  ...  http://finance.eastmoney.com/a/202404163047193...
4   300059  ...  http://finance.eastmoney.com/a/202404263060328...
..     ...  ...                                                ...
95  300059  ...  http://finance.eastmoney.com/a/202403213019923...
96  300059  ...  http://finance.eastmoney.com/a/202403143012507...
97  300059  ...  http://finance.eastmoney.com/a/202403073004835...
98  300059  ...  http://finance.eastmoney.com/a/202402282997385...
99  300059  ...  http://finance.eastmoney.com/a/202402282997353...
[100 rows x 6 columns]
```
            """
            news_info = self.code_agent.generate_and_execute_data_fetch_code(
                user_query=news_query,
                rewrite_query=news_query,
                doc_api=doc_api,
                max_iterations=reflection_nums
            )

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
                "trend_analysis": {
                    "query": trend_query,
                    "result": trend_analysis
                },
                "news_reports": {
                    "query": news_query,
                    "result": news_info
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
            trend_analysis = analysis_result['trend_analysis']
            news_reports = analysis_result['news_reports']

            
            analysis_text += f"股票名称: {stock_name}\n"
            analysis_text += f"分析时间段: {analysis_period['start_date']} 到 {analysis_period['end_date']}\n"
            analysis_text += f"公司概况数据: {company_profile['result']}\n"
            analysis_text += f"股票走势分析数据: {trend_analysis['result']}\n"
            analysis_text += f"新闻报告数据: {news_reports['result']}\n"


            print("生成报告提示词")
            report_prompt = stock_report_prompt.format(stock_data=analysis_text)
            # print(report_prompt)
            messages = [
                {"role": "system", "content": "你是一名专业的金融分析师，需要根据提供的股票数据生成一份专业、客观的股票分析报告。标题要带上分析时间段"},
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