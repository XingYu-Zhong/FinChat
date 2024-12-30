# FinChat 智能股票分析助手 🚀

## 项目简介

FinChat 是一个基于人工智能的股票分析助手，集成了多个大语言模型（如智谱 GLM-4、Deepseek），能够为用户提供专业的股票分析服务。系统通过结合实时市场数据和 AI 分析能力，为投资者提供深入的市场洞察和投资建议。

### 主要特性

- 🤖 支持多个大语言模型（GLM-4、Deepseek等）
- 📈 实时股票数据分析
- 🔍 智能市场洞察
- 💡 专业投资建议
- 🌐 友好的 Web 界面

## 项目结构

```
FinChat/
├── agent/                 # 智能代理模块
├── llm/                   # LLM 模型接口
├── promptstore/           # Prompt 模板存储
├── llamaindex/           # 向量检索相关
├── predata/              # 数据预处理
├── data/                 # 数据存储
├── .streamlit/           # Streamlit 配置
├── app.py                # Web 应用主程序
├── requirements.txt      # 项目依赖
└── .env                  # 环境变量配置
```

## 安装说明

### 环境要求

- Python 3.11+
- Conda 或 pip 包管理器

### 依赖版本

主要依赖包版本要求：
- llama_index==0.12.8
- streamlit==1.41.1
- akshare (最新版本)
- python-dotenv
- json-repair

注意：由于 akshare 的数据可能会更新，建议定期更新到最新版本：
```bash
pip install --upgrade akshare
```

### 安装步骤

1. 克隆项目
```bash
git clone [项目地址]
cd FinChat
```

2. 使用 Conda 创建虚拟环境（推荐）
```bash
# 创建名为 finchat 的 Python 3.11 环境
conda create -n finchat python=3.11
# 激活环境
conda activate finchat
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
复制 `.env_tmp` 为 `.env` 并填写必要的配置信息：
```bash
cp .env_tmp .env
```

需要配置的环境变量：
- `zhipu_api_key`: 智谱 AI API 密钥
- `zhipu_base_url`: 智谱 AI 接口地址
- `deepseek_api_key`: Deepseek API 密钥
- `deepseek_base_url`: Deepseek 接口地址

zhipu：https://open.bigmodel.cn/
deepseek：https://platform.deepseek.com/
## 使用说明

### 启动服务

```bash
# 使用默认端口（8501）启动
streamlit run app.py

# 或使用 80 端口启动（需要 root 权限）
sudo streamlit run app.py
```

### 访问应用

- 本地访问：http://localhost 或 http://localhost:8501
- 远程访问：http://[服务器IP]

### 使用流程

1. 在左侧边栏选择要使用的 LLM 模型
2. 在主界面输入股票名称
3. 选择分析的时间范围
4. 点击"开始分析"按钮
5. 等待分析结果生成

## 注意事项

- 首次运行时会下载必要的模型文件，可能需要一些时间
- 分析过程可能需要几分钟，请耐心等待
- 分析结果仅供参考，不构成投资建议
- 建议使用较短的时间范围以获得更精确的分析结果

## 许可证

本项目采用 [LICENSE](LICENSE) 许可证

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送邮件至 zhongxingyuemail@gmail.com

## 致谢

感谢以下开源项目的支持：
- Streamlit
- LlamaIndex
- AKShare