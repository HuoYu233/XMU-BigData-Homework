# Olist 巴西电商数据智能体

基于 Olist 巴西电商公开数据集的数据分析智能体（Data Agent）。

## 技术栈
Python 3.11 + pandas + MySQL + LangChain + DeepSeek API + Streamlit + Matplotlib

## 环境配置

### 1. Conda 环境
```bash
conda create -n bigdata python=3.11 -y
conda activate bigdata
```

### 2. 安装 MySQL
```bash
conda install -c conda-forge mysql-server -y
mysqld --initialize-insecure --user=$(whoami)
mysqld --user=$(whoami) &
```

### 3. 创建数据库
```bash
mysql -u root -e "CREATE DATABASE IF NOT EXISTS olist DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### 4. 安装 Python 依赖
```bash
pip install -r requirements.txt
```

### 5. 配置环境变量
编辑 `.env` 文件，填入 DeepSeek API Key:
```
DEEPSEEK_API_KEY=sk-xxx
```

### 6. 数据准备
将 Olist 数据集 CSV 文件放入 `dataset/` 目录。

## 运行步骤

```bash
# 1. 数据预处理
python scripts/01_preprocess.py

# 2. 建库建表
python scripts/02_create_db.py

# 3. 导入数据
python scripts/03_import_data.py

# 4. 启动 Web 应用
streamlit run app.py
```

打开浏览器访问 http://localhost:8501

## 项目结构
```
├── dataset/           # 原始CSV数据集（不提交）
├── data/cleaned/      # 清洗后数据
├── scripts/           # 数据处理和建库脚本
├── agent/             # Data Agent 核心
│   ├── db.py          # 数据库管理
│   ├── llm.py         # DeepSeek LLM 集成
│   ├── pipeline.py    # Agent 5步管道
│   └── prompts.py     # Prompt 模板
├── app.py             # Streamlit Web 界面
└── requirements.txt
```
