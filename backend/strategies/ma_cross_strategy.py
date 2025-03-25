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
            "position_size_percent": 10  # 默认使用10%资金
        }
        
        if parameters:
            default_params.update(parameters)
            
        super().__init__(strategy_id, name, description, default_params)
        self.last_signal_time = 0
        self.signal_cooldown = 30  # 信号冷却时间（秒）
        self.price_history = []
        
        # 初始化价格历史记录
        self.price_history = []
        self.last_signal = None  # 上一次信号：'buy' 或 'sell'
        self.last_signal_time = 0
        self.signal_cooldown = 60  # 信号冷却时间（秒）
        
    def execute(self, market_data, positions, account):
        """执行策略逻辑"""
        # 检查是否有市场数据
        if not market_data:
            self.logger.warning("无法获取市场数据")
            return None
            
        # 获取当前价格
        current_price = None
        current_time = time.time()
        symbol = self.parameters.get("symbol")
        timeframe = None
        
        # 尝试从不同格式的市场数据中提取价格
        if isinstance(market_data, dict):
            # 尝试获取交易品种和K线周期
            if "symbol" in market_data:
                symbol = market_data["symbol"]
            if "timeframe" in market_data:
                timeframe = market_data["timeframe"]
                
            if "close" in market_data:  # 回测数据格式
                current_price = float(market_data["close"])
            elif "last" in market_data:  # 实时数据格式
                current_price = float(market_data["last"])
            elif "kline" in market_data and market_data["kline"]:  # K线数据格式
                current_price = float(market_data["kline"][0][4])  # 最新K线的收盘价
            elif "data" in market_data and isinstance(market_data["data"], dict):
                # 处理嵌套的数据结构
                data = market_data["data"]
                if "symbol" in data:
                    symbol = data["symbol"]
                if "timeframe" in data:
                    timeframe = data["timeframe"]
                if "last" in data:
                    current_price = float(data["last"])
                elif "close" in data:
                    current_price = float(data["close"])
        elif isinstance(market_data, list) and market_data:
            # 处理列表格式的数据
            if isinstance(market_data[0], dict) and "close" in market_data[0]:
                current_price = float(market_data[0]["close"])
                if "symbol" in market_data[0]:
                    symbol = market_data[0]["symbol"]
                if "timeframe" in market_data[0]:
                    timeframe = market_data[0]["timeframe"]
        
        if not current_price:
            self.logger.warning(f"无法从市场数据中提取价格: {market_data}")
            return None
        
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
        
        # 计算实际仓位大小
        position_size = self.calculate_position_size(account, current_price)
        
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
                
                signal = {
                    "action": "buy",
                    "symbol": symbol,
                    "size": position_size,
                    "reason": f"金叉信号：快线上穿慢线"
                }
                
                # 添加K线周期信息
                if timeframe:
                    signal["timeframe"] = timeframe
                    
                return signal
                
            elif death_cross and self.last_signal != 'sell':
                self.last_signal = 'sell'
                self.last_signal_time = current_time
                self.logger.info(f"死叉信号：快线 {fast_ma:.2f} 下穿慢线 {slow_ma:.2f}")
                
                signal = {
                    "action": "sell",
                    "symbol": symbol,
                    "size": position_size,
                    "reason": f"死叉信号：快线下穿慢线"
                }
                
                # 添加K线周期信息
                if timeframe:
                    signal["timeframe"] = timeframe
                    
                return signal
                
        return None

    def generate_signal(self, market_data, positions, account):
        """
        生成交易信号
        
        Args:
            market_data: 市场数据
            positions: 当前持仓
            account: 账户信息
        
        Returns:
            交易信号
        """
        try:
            # 检查是否有足够的市场数据
            if not market_data:
                self.logger.warning("无法获取市场数据")
                return None
            
            # 获取当前价格
            current_price = None
            symbol = self.parameters.get("symbol")
            timeframe = None
            
            if isinstance(market_data, dict):
                # 尝试获取交易品种和K线周期
                if "symbol" in market_data:
                    symbol = market_data["symbol"]
                if "timeframe" in market_data:
                    timeframe = market_data["timeframe"]
                    
                if "close" in market_data:  # 回测数据格式
                    current_price = float(market_data["close"])
                elif "last" in market_data:  # 实时数据格式
                    current_price = float(market_data["last"])
                elif "kline" in market_data and market_data["kline"]:  # K线数据格式
                    current_price = float(market_data["kline"][0][4])  # 最新K线的收盘价
                elif "data" in market_data and isinstance(market_data["data"], dict):
                    data = market_data["data"]
                    if "symbol" in data:
                        symbol = data["symbol"]
                    if "timeframe" in data:
                        timeframe = data["timeframe"]
                    if "last" in data:
                        current_price = float(data["last"])
                    elif "close" in data:
                        current_price = float(data["close"])
            
            if not current_price:
                self.logger.warning("无法获取当前价格")
                return None
            
            # 获取参数
            fast_period = int(self.parameters.get("fast_period", 5))
            slow_period = int(self.parameters.get("slow_period", 20))
            
            # 计算实际仓位大小
            position_size = self.calculate_position_size(account, current_price)
            
            # 更新价格历史
            self.price_history.append(current_price)
            
            # 保持价格历史长度不超过慢速均线周期
            if len(self.price_history) > slow_period:
                self.price_history = self.price_history[-slow_period:]
            
            # 如果价格历史不足以计算均线，则返回
            if len(self.price_history) < slow_period:
                return None
            
            # 计算快速均线
            fast_ma = sum(self.price_history[-fast_period:]) / fast_period
            
            # 计算慢速均线
            slow_ma = sum(self.price_history[-slow_period:]) / slow_period
            
            # 检查是否已有持仓
            has_position = False
            position_side = None
            for position in positions:
                pos_symbol = position.get("symbol", position.get("instId", ""))
                if pos_symbol == symbol:
                    has_position = True
                    position_side = position.get("side", "long" if float(position.get("pos", 0)) > 0 else "short")
                    break
            
            # 均线交叉策略逻辑
            # 快线上穿慢线，买入信号
            if fast_ma > slow_ma and not has_position:
                signal = {
                    "action": "buy",
                    "symbol": symbol,
                    "size": position_size,
                    "reason": f"均线金叉: 快线 {fast_ma:.2f} > 慢线 {slow_ma:.2f}"
                }
                
                # 添加K线周期信息
                if timeframe:
                    signal["timeframe"] = timeframe
                    
                return signal
            
            # 快线下穿慢线，卖出信号
            elif fast_ma < slow_ma and has_position and position_side == "long":
                signal = {
                    "action": "sell",
                    "symbol": symbol,
                    "size": position_size,
                    "reason": f"均线死叉: 快线 {fast_ma:.2f} < 慢线 {slow_ma:.2f}"
                }
                
                # 添加K线周期信息
                if timeframe:
                    signal["timeframe"] = timeframe
                    
                return signal
            
            return None
        except Exception as e:
            self.logger.error(f"生成均线交叉信号错误: {str(e)}")
            return None