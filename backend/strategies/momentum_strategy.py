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
            "position_size": 1
        }
        
        if parameters:
            default_params.update(parameters)
            
        super().__init__(strategy_id, name, description, default_params)
        self.last_signal_time = 0
        self.signal_cooldown = 60  # 信号冷却时间（秒）
    
    def generate_signal(self, market_data, positions, account):
        """
        生成交易信号
        
        :param market_data: 市场数据
        :param positions: 持仓数据
        :param account: 账户数据
        :return: 交易信号或None
        """
        # 检查是否有市场数据
        if not market_data or "kline" not in market_data or not market_data["kline"]:
            self.logger.warning("无法获取K线数据")
            return None
            
        # 获取参数
        lookback_period = int(self.parameters["lookback_period"])
        threshold = float(self.parameters["threshold"])
        
        # 信号冷却检查
        current_time = time.time()
        if current_time - self.last_signal_time < self.signal_cooldown:
            return None
            
        # 获取K线数据
        klines = market_data["kline"]
        if len(klines) < lookback_period + 1:
            self.logger.warning(f"K线数据不足，需要至少 {lookback_period + 1} 条")
            return None
            
        # 计算价格变化
        current_price = float(klines[0][4])  # 当前收盘价
        past_price = float(klines[lookback_period][4])  # 过去的收盘价
        price_change = (current_price - past_price) / past_price
        
        # 检查是否有持仓
        has_position = False
        for position in positions:
            if position.get("instId") == self.parameters["symbol"] and float(position.get("pos", 0)) > 0:
                has_position = True
                break
                
        # 生成信号
        if price_change > threshold and not has_position:
            # 价格上涨超过阈值，生成买入信号
            self.last_signal_time = current_time
            self.logger.info(f"价格上涨 {price_change:.2%}，生成买入信号")
            return {
                "action": "buy",
                "symbol": self.parameters["symbol"],
                "size": str(self.parameters["position_size"]),
                "reason": f"价格上涨 {price_change:.2%}"
            }
        elif price_change < -threshold and has_position:
            # 价格下跌超过阈值，生成卖出信号
            self.last_signal_time = current_time
            self.logger.info(f"价格下跌 {-price_change:.2%}，生成卖出信号")
            return {
                "action": "sell",
                "symbol": self.parameters["symbol"],
                "size": str(self.parameters["position_size"]),
                "reason": f"价格下跌 {-price_change:.2%}"
            }
            
        return None
        
    def execute(self, market_data, positions, account):
        """执行策略逻辑"""
        return self.generate_signal(market_data, positions, account)