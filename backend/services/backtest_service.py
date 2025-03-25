# ... 现有代码 ...

def run_backtest(strategy_id, start_time, end_time, symbol, timeframe, initial_balance=10000):
    """运行回测"""
    try:
        # 获取策略
        strategy = strategy_service.get_strategy(strategy_id)
        if not strategy:
            return {"success": False, "msg": "策略不存在"}
            
        # 获取市场数据
        market_data = market_data_service.get_historical_data(symbol, timeframe, start_time, end_time)
        if not market_data:
            return {"success": False, "msg": "无法获取市场数据"}
        
        print(f"回测服务 - 交易品种: {symbol}, K线周期: {timeframe}")
            
        # 运行回测 - 直接接收四个返回值
        trades, account_history, backtest_symbol, backtest_timeframe = backtest_engine.run_backtest(
            strategy, 
            market_data, 
            initial_balance,
            symbol,
            timeframe
        )
        
        print(f"回测引擎返回 - 交易品种: {backtest_symbol}, K线周期: {backtest_timeframe}")
        
        # 生成回测结果
        result = generate_backtest_result(
            strategy, 
            trades, 
            account_history, 
            market_data,
            backtest_symbol,  # 使用回测引擎返回的交易品种
            backtest_timeframe  # 使用回测引擎返回的K线周期
        )
        
        # 保存回测结果
        backtest_id = save_backtest_result(strategy_id, result)
        
        return {
            "success": True,
            "backtest_id": backtest_id,
            "result": result
        }
    except Exception as e:
        logger.error(f"回测错误: {str(e)}")
        return {"success": False, "msg": f"回测错误: {str(e)}"}

def generate_backtest_result(strategy, trades, account_history, market_data, symbol, timeframe):
    """生成回测结果"""
    if not account_history:
        return {
            "overview": {
                "symbol": str(symbol) if symbol else "未知",  # 确保转换为字符串
                "timeframe": str(timeframe) if timeframe else "未知",  # 确保转换为字符串
                "start_time": "",
                "end_time": "",
                "initial_balance": 0,
                "final_balance": 0,
                "total_return": 0,
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "profit_factor": 0,
                "max_drawdown": 0
            },
            "trades": [],
            "equity_curve": []
        }
    
    print(f"生成回测结果 - 交易品种: {symbol}, K线周期: {timeframe}")
    
    # 计算回测结果
    initial_balance = account_history[0]["balance"]
    final_balance = account_history[-1]["balance"]
    total_return = (final_balance - initial_balance) / initial_balance if initial_balance > 0 else 0
    
    # 计算交易统计
    total_trades = len(trades)
    winning_trades = sum(1 for trade in trades if trade.get("profit", 0) > 0)
    losing_trades = sum(1 for trade in trades if trade.get("profit", 0) <= 0)
    win_rate = winning_trades / total_trades if total_trades > 0 else 0
    
    # 计算盈亏比
    total_profit = sum(trade.get("profit", 0) for trade in trades if trade.get("profit", 0) > 0)
    total_loss = abs(sum(trade.get("profit", 0) for trade in trades if trade.get("profit", 0) < 0))
    profit_factor = total_profit / total_loss if total_loss > 0 else 0
    
    # 计算最大回撤
    max_drawdown = 0
    peak = initial_balance
    for record in account_history:
        if record["equity"] > peak:
            peak = record["equity"]
        drawdown = (peak - record["equity"]) / peak if peak > 0 else 0
        max_drawdown = max(max_drawdown, drawdown)
    
    # 获取开始和结束时间
    start_time = market_data[0]["timestamp"] if market_data else ""
    end_time = market_data[-1]["timestamp"] if market_data else ""
    
    # 确保交易品种和K线周期是字符串类型
    symbol_str = str(symbol) if symbol else "未知"
    timeframe_str = str(timeframe) if timeframe else "未知"
    
    # 构建回测概览
    overview = {
        "symbol": symbol_str,  # 使用字符串类型的交易品种
        "timeframe": timeframe_str,  # 使用字符串类型的K线周期
        "start_time": start_time,
        "end_time": end_time,
        "initial_balance": initial_balance,
        "final_balance": final_balance,
        "total_return": total_return,
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "max_drawdown": max_drawdown
    }
    
    print(f"回测概览 - 交易品种: {overview['symbol']}, K线周期: {overview['timeframe']}")
    
    # 构建权益曲线数据
    equity_curve = [
        {
            "timestamp": record["timestamp"],
            "balance": record["balance"],
            "equity": record["equity"]
        }
        for record in account_history
    ]
    
    # 构建回测结果
    result = {
        "overview": overview,
        "trades": trades,
        "equity_curve": equity_curve
    }
    
    return result