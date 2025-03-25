from .base_strategy import BaseStrategy
import time
import importlib.util
import sys
import os
import uuid
import logging

class CustomStrategy(BaseStrategy):
    """
    自定义策略：通过直接编写Python代码实现的策略
    
    参数:
    - symbol: 交易品种
    - code: 策略代码
    - position_size: 仓位大小
    """
    
    def __init__(self, strategy_id, name="自定义策略", description="通过直接编写代码实现的策略", parameters=None):
        default_params = {
            "symbol": "BTC-USDT-SWAP",
            "code": "",
            "position_size": 1
        }
        
        if parameters:
            default_params.update(parameters)
            
        super().__init__(strategy_id, name, description, default_params)
        self.last_signal_time = 0
        self.signal_cooldown = 30  # 信号冷却时间（秒）
        self.strategy_module = None
        self._load_strategy_code()
        
    def _load_strategy_code(self):
        """加载策略代码"""
        try:
            code = self.parameters.get("code", "")
            if not code:
                self.logger.warning("策略代码为空")
                return
                
            # 创建临时文件存储策略代码
            strategy_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "custom_strategies")
            os.makedirs(strategy_dir, exist_ok=True)
            
            module_name = f"custom_strategy_{self.strategy_id}"
            file_path = os.path.join(strategy_dir, f"{module_name}.py")
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
                
            # 动态加载模块
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 检查模块是否包含必要的函数
            if not hasattr(module, "execute_strategy"):
                self.logger.error("策略代码必须包含execute_strategy函数")
                return
                
            self.strategy_module = module
            self.logger.info("策略代码加载成功")
            
        except Exception as e:
            self.logger.error(f"加载策略代码错误: {str(e)}")
            
    def update_parameters(self, parameters):
        """更新策略参数"""
        super().update_parameters(parameters)
        # 如果代码更新了，重新加载
        if "code" in parameters:
            self._load_strategy_code()
            
    def execute(self, market_data, positions, account):
        """执行策略逻辑"""
        current_time = time.time()
        
        # 信号冷却检查
        if current_time - self.last_signal_time < self.signal_cooldown:
            return None
            
        if not self.strategy_module:
            self.logger.warning("策略模块未加载")
            return None
            
        try:
            # 获取当前价格和交易品种、K线周期
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
            
            # 计算实际仓位大小
            position_size = self.calculate_position_size(account, current_price) if current_price else 1
            
            # 更新参数中的实际仓位大小和交易品种
            parameters = self.parameters.copy()
            parameters["position_size"] = position_size
            parameters["symbol"] = symbol
            
            # 添加K线周期信息
            if timeframe:
                parameters["timeframe"] = timeframe
            
            # 调用自定义策略代码
            result = self.strategy_module.execute_strategy(
                market_data=market_data,
                positions=positions,
                account=account,
                parameters=parameters,
                logger=self.logger
            )
            
            if result and "action" in result:
                # 确保信号包含交易品种和K线周期信息
                if "symbol" not in result:
                    result["symbol"] = symbol
                if timeframe and "timeframe" not in result:
                    result["timeframe"] = timeframe
                    
                self.last_signal_time = current_time
                return result
                
            return None
            
        except Exception as e:
            self.logger.error(f"执行自定义策略错误: {str(e)}")
            return None
            
    def generate_signal(self, market_data, positions, account):
        """生成交易信号"""
        # 直接调用execute方法，不要再调用generate_signal，避免循环调用
        return self.execute(market_data, positions, account)