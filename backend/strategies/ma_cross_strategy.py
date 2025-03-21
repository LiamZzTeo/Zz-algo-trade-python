from .base_strategy import BaseStrategy
import numpy as np
import time

class MACrossStrategy(BaseStrategy):
    """
    均线交叉策略：当快速均线上穿慢速均线时买入，下穿时卖出
    
    参数:
    - symbol: 交易品种
    - fast_period: 快速均线周期
    - slow_period: 慢速均线周期
    - position_size: 仓位大小
    """
    
    def __init__(self, strategy_id, name="均线交叉策略", description="基于快慢均线交叉的交易策略", parameters=None):
        default_params = {
            "symbol": "BTC-USDT-SWAP",
            "fast_period": 5,
            "slow_period": 20,
            "position_size": 1
        }
        
        if parameters:
            default_params.update(parameters)
            
        super().__init__(strategy_id, name, description, default_params)
        
        # 初始化价格历史记录
        self.price_history = []
        self.last_signal = None  # 上一次信号：'buy' 或 'sell'
        self.last_signal_time = 0
        self.signal_cooldown = 60  # 信号冷却时间（秒）
        
    def execute(self, market_data, positions, account):
        """执行策略逻辑"""
        # 检查是否有市场数据
        if not market_data or "last" not in market_data:
            self.logger.warning("无法获取市场数据")
            return None
            
        # 获取当前价格
        current_price = float(market_data["last"])
        current_time = time.time()
        
        # 更新价格历史
        self.price_history.append(current_price)
        
        # 保持历史记录长度
        slow_period = int(self.parameters["slow_period"])
        if len(self.price_history) > slow_period * 3:  # 保留足够的历史数据
            self.price_history = self.price_history[-slow_period*3:]
        
        # 如果历史记录不足，无法计算均线
        if len(self.price_history) < slow_period:
            return None
            
        # 计算快速均线和慢速均线
        fast_period = int(self.parameters["fast_period"])
        fast_ma = np.mean(self.price_history[-fast_period:])
        slow_ma = np.mean(self.price_history[-slow_period:])
        
        # 如果历史记录足够，计算前一个时间点的均线
        if len(self.price_history) > slow_period + 1:
            prev_fast_ma = np.mean(self.price_history[-(fast_period+1):-1])
            prev_slow_ma = np.mean(self.price_history[-(slow_period+1):-1])
            
            # 检查是否有交叉
            golden_cross = prev_fast_ma <= prev_slow_ma and fast_ma > slow_ma  # 金叉：快线上穿慢线
            death_cross = prev_fast_ma >= prev_slow_ma and fast_ma < slow_ma   # 死叉：快线下穿慢线
            
            # 信号冷却检查
            if current_time - self.last_signal_time < self.signal_cooldown:
                return None
                
            # 生成交易信号
            if golden_cross and self.last_signal != 'buy':
                self.last_signal = 'buy'
                self.last_signal_time = current_time
                self.logger.info(f"金叉信号：快线 {fast_ma:.2f} 上穿慢线 {slow_ma:.2f}")
                
                return {
                    "action": "buy",
                    "symbol": self.parameters["symbol"],
                    "size": str(self.parameters["position_size"]),
                    "reason": f"金叉信号：快线上穿慢线"
                }
                
            elif death_cross and self.last_signal != 'sell':
                self.last_signal = 'sell'
                self.last_signal_time = current_time
                self.logger.info(f"死叉信号：快线 {fast_ma:.2f} 下穿慢线 {slow_ma:.2f}")
                
                return {
                    "action": "sell",
                    "symbol": self.parameters["symbol"],
                    "size": str(self.parameters["position_size"]),
                    "reason": f"死叉信号：快线下穿慢线"
                }
                
        return None