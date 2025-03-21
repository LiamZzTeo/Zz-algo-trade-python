# AlgoSysTest - 量化交易系统

一个基于React和Python的量化交易系统，支持多种交易策略和实时市场数据监控。

## 功能特点

- 多种预设交易策略（动量策略、网格策略、均线交叉策略）
- 支持自定义策略开发
- 实时市场数据监控
- 账户资产和持仓管理
- 交易执行和历史记录

## 技术栈

### 前端
- React
- Ant Design
- JavaScript/ES6+

### 后端
- Python
- FastAPI
- OKX API

## 安装和使用

### 前端
```bash
cd frontend
npm install
npm start
```

### 后端
```bash
cd backend
pip install -r requirements.txt
python main.py
 ```


## 配置
在项目根目录创建.env文件，添加以下配置：

```plaintext
API_KEY=您的OKX API密钥
API_SECRET=您的OKX API密钥
PASSPHRASE=您的OKX API密码
 ```
