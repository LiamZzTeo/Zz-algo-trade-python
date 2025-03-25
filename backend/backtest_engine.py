import time
import datetime
import pandas as pd
import numpy as np
from copy import deepcopy

class BacktestEngine:
    """
    回测引擎：用于对策略进行历史数据回测
    """
    
    def __init__(self, okx_client):
        """
        初始化回测引擎
        
        Args:
            okx_client: OKX API客户端实例
        """
        self.okx_client = okx_client
        
    def run_backtest(self, strategy, symbol, bar="1m", initial_capital=10000):
        """
        运行回测
        
        Args:
            strategy: 策略实例
            symbol: 交易对
            bar: K线周期
            initial_capital: 初始资金
        
        Returns:
            回测结果
        """
        try:
            print(f"开始回测: 策略={strategy.name}, 交易对={symbol}, 周期={bar}, 初始资金={initial_capital}")
            
            # 获取历史K线数据
            candles_result = self.okx_client.get_historical_candles(symbol, bar)
            
            if not candles_result["success"]:
                print(f"获取历史K线数据失败: {candles_result['msg']}")
                return {"success": False, "msg": f"获取历史K线数据失败: {candles_result['msg']}"}
            
            candles = candles_result["data"]
            
            if not candles:
                print("没有获取到历史K线数据")
                return {"success": False, "msg": "没有获取到历史K线数据"}
            
            print(f"获取到 {len(candles)} 条历史K线数据")
            
            # 初始化回测数据
            backtest_data = {
                "initial_capital": initial_capital,
                "current_capital": initial_capital,
                "positions": [],
                "trades": [],
                "equity_curve": []
            }
            
            # 模拟账户
            account = {
                "balance": initial_capital,
                "equity": initial_capital,
                "available": initial_capital
            }
            
            # 持仓
            positions = []
            
            # 遍历K线数据
            for i, candle in enumerate(candles):
                # 构建市场数据
                market_data = {
                    "symbol": symbol,
                    "timestamp": candle["timestamp"],
                    "open": candle["open"],
                    "high": candle["high"],
                    "low": candle["low"],
                    "close": candle["close"],
                    "volume": candle["volume"]
                }
                
                # 执行策略
                signal = strategy.execute(market_data, positions, account)
                
                # 处理信号
                if signal:
                    self._process_signal(signal, candle, backtest_data, positions, account)
                
                # 更新账户权益
                self._update_equity(candle, backtest_data, positions, account)
            
            # 计算回测结果
            result = self._calculate_results(backtest_data)
            
            return {"success": True, "data": result}
        except Exception as e:
            print(f"回测过程中出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "msg": f"回测过程中出错: {str(e)}"}


    def _update_equity(self, candle, backtest_data, positions, account):
        """
        更新账户权益
        
        Args:
            candle: 当前K线数据
            backtest_data: 回测数据
            positions: 持仓列表
            account: 账户信息
        """
        # 计算当前权益
        equity = account["balance"]
        
        # 加上未实现盈亏
        for position in positions:
            if position["size"] > 0:
                # 多头持仓
                if position["side"] == "long":
                    unrealized_pnl = position["size"] * (candle["close"] - position["entry_price"])
                # 空头持仓
                else:
                    unrealized_pnl = position["size"] * (position["entry_price"] - candle["close"])
                
                equity += unrealized_pnl
        
        # 更新账户权益
        account["equity"] = equity
        
        # 记录权益曲线
        backtest_data["equity_curve"].append({
            "timestamp": candle["timestamp"],
            "equity": equity
        })

    def _process_signal(self, signal, candle, backtest_data, positions, account):
        """
        处理交易信号
        
        Args:
            signal: 交易信号
            candle: 当前K线数据
            backtest_data: 回测数据
            positions: 持仓列表
            account: 账户信息
        """
        if not signal:
            return
        
        # 处理开仓信号
        if signal["action"] in ["buy", "long", "sell", "short"]:
            # 获取仓位大小
            position_size = float(signal.get("size", 1))
            
            # 检查是否有足够的资金
            required_margin = position_size * candle["close"] * 0.1  # 假设10%保证金
            if account["available"] < required_margin:
                print(f"资金不足，无法开仓: 需要 {required_margin}，可用 {account['available']}")
                return
            
            # 创建新持仓
            position = {
                "symbol": signal.get("symbol", candle.get("symbol")),
                "side": "long" if signal["action"] in ["buy", "long"] else "short",
                "size": position_size,
                "entry_price": candle["close"],
                "entry_time": candle["timestamp"]
            }
            
            # 添加到持仓列表
            positions.append(position)
            
            # 更新账户可用资金
            account["available"] -= required_margin
            
            # 记录交易
            trade = {
                "timestamp": candle["timestamp"],
                "symbol": position["symbol"],
                "action": signal["action"],
                "price": candle["close"],
                "size": position["size"],
                "profit": 0
            }
            
            backtest_data["trades"].append(trade)
        
        # 处理平仓信号
        elif signal["action"] in ["close_long", "close_short"]:
            # 查找对应的持仓
            position_idx = -1
            for i, pos in enumerate(positions):
                if (signal["action"] == "close_long" and pos["side"] == "long") or \
                (signal["action"] == "close_short" and pos["side"] == "short"):
                    position_idx = i
                    break
            
            if position_idx >= 0:
                position = positions.pop(position_idx)
                
                # 计算盈亏
                if position["side"] == "long":
                    profit = position["size"] * (candle["close"] - position["entry_price"])
                else:
                    profit = position["size"] * (position["entry_price"] - candle["close"])
                
                # 更新账户余额和可用资金
                account["balance"] += profit
                account["available"] += (position["size"] * candle["close"] * 0.1) + profit  # 返还保证金 + 盈亏
                
                # 记录交易
                trade = {
                    "timestamp": candle["timestamp"],
                    "symbol": position["symbol"],
                    "action": signal["action"],
                    "price": candle["close"],
                    "size": position["size"],
                    "profit": profit
                }
                
                backtest_data["trades"].append(trade)

    def _calculate_results(self, backtest_data):
        """
        计算回测结果
        
        Args:
            backtest_data: 回测数据
        
        Returns:
            回测结果统计
        """
        # 初始化结果
        result = {
            "initial_capital": backtest_data["initial_capital"],
            "final_equity": backtest_data["current_capital"],
            "total_return": 0,
            "max_drawdown": 0,
            "total_trades": len(backtest_data["trades"]),
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0,
            "total_profit": 0,
            "max_profit_trade": 0,
            "max_loss_trade": 0,
            "sharpe_ratio": 0,
            "equity_curve": backtest_data["equity_curve"],
            "trades": backtest_data["trades"]
        }
        
        # 如果没有交易，直接返回
        if not backtest_data["trades"]:
            return result
        
        # 计算交易统计
        profits = []
        for trade in backtest_data["trades"]:
            profit = trade.get("profit", 0)
            if profit > 0:
                result["winning_trades"] += 1
                result["max_profit_trade"] = max(result["max_profit_trade"], profit)
            elif profit < 0:
                result["losing_trades"] += 1
                result["max_loss_trade"] = min(result["max_loss_trade"], profit)
            
            result["total_profit"] += profit
            profits.append(profit)
        
        # 计算胜率
        if result["total_trades"] > 0:
            result["win_rate"] = (result["winning_trades"] / result["total_trades"]) * 100
        
        # 计算总收益率
        if backtest_data["initial_capital"] > 0:
            result["total_return"] = (result["total_profit"] / backtest_data["initial_capital"]) * 100
        
        # 计算最大回撤
        if backtest_data["equity_curve"]:
            max_equity = backtest_data["equity_curve"][0]["equity"]
            current_drawdown = 0
            
            for point in backtest_data["equity_curve"]:
                equity = point["equity"]
                max_equity = max(max_equity, equity)
                current_drawdown = (max_equity - equity) / max_equity * 100
                result["max_drawdown"] = max(result["max_drawdown"], current_drawdown)
        
        # 计算夏普比率 (简化版)
        if profits and len(profits) > 1:
            import numpy as np
            returns = np.array(profits) / backtest_data["initial_capital"]
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            if std_return > 0:
                result["sharpe_ratio"] = mean_return / std_return * np.sqrt(252)  # 假设252个交易日
        
        # 添加开始和结束时间
        if backtest_data["equity_curve"]:
            start_time = backtest_data["equity_curve"][0]["timestamp"]
            end_time = backtest_data["equity_curve"][-1]["timestamp"]
            
            # 转换为可读时间格式
            import datetime
            result["start_time"] = datetime.datetime.fromtimestamp(start_time / 1000).strftime('%Y-%m-%d %H:%M:%S')
            result["end_time"] = datetime.datetime.fromtimestamp(end_time / 1000).strftime('%Y-%m-%d %H:%M:%S')
        
        return result