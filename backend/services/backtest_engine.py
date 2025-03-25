# ... 现有代码 ...

def run_backtest(strategy, market_data, initial_balance=10000, symbol=None, timeframe=None):
    """运行回测"""
    # 初始化账户和持仓
    account = {"balance": initial_balance, "equity": initial_balance}
    positions = []
    trades = []
    account_history = [{"timestamp": market_data[0]["timestamp"] if market_data else 0, "balance": initial_balance, "equity": initial_balance}]
    
    # 如果没有提供交易品种和K线周期，尝试从策略参数中获取
    if symbol is None and hasattr(strategy, 'parameters'):
        symbol = strategy.parameters.get("symbol")
    
    if timeframe is None and hasattr(strategy, 'parameters'):
        timeframe = strategy.parameters.get("timeframe", "1m")
    
    print(f"回测引擎 - 使用交易品种: {symbol}, K线周期: {timeframe}")
    
    # 执行策略
    for data in market_data:
        # 确保市场数据包含交易品种和K线周期信息
        if isinstance(data, dict):
            if "symbol" not in data and symbol:
                data["symbol"] = symbol
            if "timeframe" not in data and timeframe:
                data["timeframe"] = timeframe
        
        # 执行策略
        signal = strategy.execute(data, positions, account)
        
        # 处理信号
        if signal:
            # 确保信号包含交易品种和K线周期
            if "symbol" not in signal and symbol:
                signal["symbol"] = symbol
            if "timeframe" not in signal and timeframe:
                signal["timeframe"] = timeframe
                
            # 处理交易信号
            # ... 其他处理信号的代码 ...
            
            # 记录交易
            trade = {
                "timestamp": data.get("timestamp", 0),
                "symbol": signal.get("symbol", symbol),
                "timeframe": signal.get("timeframe", timeframe),
                # ... 其他交易信息 ...
            }
            trades.append(trade)
        
        # 更新账户历史
        account_history.append({
            "timestamp": data.get("timestamp", 0),
            "balance": account["balance"],
            "equity": account["equity"]
        })
    
    # 将交易品种和K线周期添加到返回的数据中
    metadata = {
        "symbol": symbol,
        "timeframe": timeframe
    }
    
    # 返回交易记录、账户历史和元数据
    return trades, account_history, metadata