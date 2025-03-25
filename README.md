# 量化交易系统 - AlgoSysTest（Demo）

AlgoSysTest 是一个功能完整的量化交易系统，支持多种交易策略的回测和实盘交易。系统基于 Python 和 React 构建，通过 OKX 交易所 API 实现交易功能。
当前项目基于OKX交易所模拟交易API进行。

## 系统特点

- **多策略支持**：内置动量策略、网格策略、均线交叉策略等
- **实时数据监控**：实时显示账户资产、持仓信息和市场行情
- **策略回测**：支持历史数据回测，评估策略表现
- **可视化界面**：直观的 Web 界面，方便策略管理和监控
- **模拟交易**：支持 OKX 模拟交易环境，无需真实资金即可测试策略

## 系统架构

```
AlgoSysTest/
├── backend/                # 后端服务
│   ├── strategies/         # 策略实现
│   │   ├── base_strategy.py       # 策略基类
│   │   ├── momentum_strategy.py   # 动量策略
│   │   └── ...
│   ├── data/               # 数据存储
│   ├── okx_client.py       # 交易所API客户端
│   ├── strategy_engine.py  # 策略引擎
│   ├── backtest_engine.py  # 回测引擎
│   └── main.py             # 主程序入口
└── frontend/               # 前端界面
    ├── src/
    │   ├── components/     # UI组件
    │   ├── hooks/          # React钩子
    │   └── ...
    └── ...
```

## 动量策略示例

动量策略是一种基于价格变化趋势进行交易的策略。当价格在一定时间内上涨超过设定阈值时买入，下跌超过阈值时卖出。

```python
# 策略核心逻辑
# 计算价格变化百分比
price_change = (current_price - self.price_history[-lookback_period]) / self.price_history[-lookback_period]

# 如果价格上涨超过阈值，且没有持仓，则买入
if price_change > threshold and not has_position:
    signal = {
        "action": "buy",
        "symbol": symbol,
        "size": position_size,
        "reason": f"价格上涨 {price_change:.2%}，超过阈值 {threshold:.2%}"
    }
    return signal
    
# 如果价格下跌超过阈值，且有持仓，则卖出
elif price_change < -threshold and has_position:
    signal = {
        "action": "sell",
        "symbol": symbol,
        "size": position_size,
        "reason": f"价格下跌 {price_change:.2%}，超过阈值 {threshold:.2%}"
    }
    return signal
```

## 系统演示
![image](https://github.com/user-attachments/assets/b5bcc654-57c8-4c9c-8d8a-11563bbd9623)
![image](https://github.com/user-attachments/assets/ce8cae7a-b628-4e38-b61b-ac2dee7cd491)
![image](https://github.com/user-attachments/assets/9f19d33d-e3a6-40d3-8ba0-4f36ebe627f2)
![image](https://github.com/user-attachments/assets/b362bab7-928b-410c-ae25-af51eb020601)
![image](https://github.com/user-attachments/assets/3d7b202d-d61f-460b-b854-3ea5674da08f)




## 安装与使用

### 前提条件

- Python 3.8+
- Node.js 14+
- OKX API 密钥 (当前测试)

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/yourusername/AlgoSysTest.git
cd AlgoSysTest
```

2. 安装后端依赖
```bash
cd backend
pip install -r requirements.txt
```

3. 安装前端依赖
```bash
cd frontend
npm install
```

4. 配置环境变量
创建 `.env` 文件，添加 OKX API 凭证

5. 启动系统
```bash
# 启动后端
cd backend
python main.py

# 启动前端
cd frontend
npm start
```

## 策略开发

系统支持自定义策略开发，只需继承 `BaseStrategy` 类并实现相应方法。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 邮箱：liam_zhang77@foxmail.com
