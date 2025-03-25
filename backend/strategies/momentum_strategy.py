from .base_strategy import BaseStrategy
import time

class MomentumStrategy(BaseStrategy):
    """
    动量策略：基于价格变化趋势进行交易
    
    参数:
    - symbol: 交易品种
    - lookback_period: 回溯周期（分钟）
    - threshold: 价格变化阈值
    - position_size: 仓位大小
    """
    
    def __init__(self, strategy_id, name="动量策略", description="基于价格动量的交易策略", parameters=None):
        default_params = {
            "symbol": "BTC-USDT-SWAP",
            "lookback_period": 5,
            "threshold": 0.01,
            "position_size_percent": 10  # 默认使用10%资金
        }
        
        if parameters:
            default_params.update(parameters)
            
        super().__init__(strategy_id, name, description, default_params)
        self.last_signal_time = 0
        self.signal_cooldown = 30  # 信号冷却时间（秒）
        self.price_history = []  # 初始化价格历史
    
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
        
        # 尝试从不同格式的市场数据中提取价格和交易品种、K线周期
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
        
        # 计算实际仓位大小
        position_size = self.calculate_position_size(account, current_price)
        
        # 信号冷却检查
        if current_time - self.last_signal_time < self.signal_cooldown:
            return None
            
        # 获取参数
        lookback_period = int(self.parameters["lookback_period"])
        threshold = float(self.parameters["threshold"])
        
        # 更新价格历史
        if hasattr(self, 'price_history'):
            self.price_history.append(current_price)
            if len(self.price_history) > lookback_period * 2:
                self.price_history = self.price_history[-lookback_period*2:]
        else:
            self.price_history = [current_price]
            
        # 如果历史记录不足，无法计算动量
        if len(self.price_history) < lookback_period:
            return None
            
        # 计算价格变化百分比
        price_change = (current_price - self.price_history[-lookback_period]) / self.price_history[-lookback_period]
        
        # 检查是否有持仓
        has_position = False
        for position in positions:
            if position.get("instId") == symbol and float(position.get("pos", 0)) > 0:
                has_position = True
                break
                
        # 生成交易信号
        if price_change > threshold and not has_position:
            self.last_signal_time = current_time
            self.logger.info(f"价格上涨 {price_change:.2%}，超过阈值 {threshold:.2%}，生成买入信号")
            
            signal = {
                "action": "buy",
                "symbol": symbol,
                "size": position_size,
                "reason": f"价格上涨 {price_change:.2%}"
            }
            
            # 添加K线周期信息
            if timeframe:
                signal["timeframe"] = timeframe
                
            return signal
            
        elif price_change < -threshold and has_position:
            self.last_signal_time = current_time
            self.logger.info(f"价格下跌 {price_change:.2%}，超过阈值 {threshold:.2%}，生成卖出信号")
            
            signal = {
                "action": "sell",
                "symbol": symbol,
                "size": position_size,
                "reason": f"价格下跌 {price_change:.2%}"
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
            lookback_period = int(self.parameters.get("lookback_period", 5))
            threshold = float(self.parameters.get("threshold", 0.01))
            
            # 计算实际仓位大小
            position_size = self.calculate_position_size(account, current_price)
            
            # 更新价格历史
            if hasattr(self, 'price_history'):
                self.price_history.append(current_price)
                if len(self.price_history) > lookback_period * 2:
                    self.price_history = self.price_history[-lookback_period*2:]
            else:
                self.price_history = [current_price]
            
            # 如果历史记录不足，无法计算动量
            if len(self.price_history) < lookback_period:
                return None
            
            # 计算价格变化百分比
            price_change = (current_price - self.price_history[-lookback_period]) / self.price_history[-lookback_period]
            
            # 检查是否已有持仓
            has_position = False
            position_side = None
            for position in positions:
                pos_symbol = position.get("symbol", position.get("instId", ""))
                if pos_symbol == symbol:
                    has_position = True
                    position_side = position.get("side", "long" if float(position.get("pos", 0)) > 0 else "short")
                    break
            
            # 动量策略逻辑
            # 如果价格上涨超过阈值，且没有多头持仓，则开多
            if price_change > threshold and not has_position:
                signal = {
                    "action": "buy",
                    "symbol": symbol,
                    "size": position_size,
                    "reason": f"价格上涨 {price_change:.2%}，超过阈值 {threshold:.2%}"
                }
                
                # 添加K线周期信息
                if timeframe:
                    signal["timeframe"] = timeframe
                    
                return signal
            
            # 如果价格下跌超过阈值，且有多头持仓，则平多
            elif price_change < -threshold and has_position and position_side == "long":
                signal = {
                    "action": "sell",
                    "symbol": symbol,
                    "size": position_size,
                    "reason": f"价格下跌 {price_change:.2%}，超过阈值 {threshold:.2%}"
                }
                
                # 添加K线周期信息
                if timeframe:
                    signal["timeframe"] = timeframe
                    
                return signal
            
            return None
        except Exception as e:
            self.logger.error(f"生成动量策略信号错误: {str(e)}")
            return None