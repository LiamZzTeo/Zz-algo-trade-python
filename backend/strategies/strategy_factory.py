from .momentum_strategy import MomentumStrategy
from .grid_strategy import GridStrategy
from .ma_cross_strategy import MACrossStrategy
from .base_strategy import BaseStrategy
from .custom_strategy import CustomStrategy

class StrategyFactory:
    """
    策略工厂：用于创建不同类型的策略实例
    """
    
    @staticmethod
    def create_strategy(strategy_type, strategy_id, name=None, description=None, parameters=None):
        """
        创建策略实例
        
        :param strategy_type: 策略类型
        :param strategy_id: 策略ID
        :param name: 策略名称
        :param description: 策略描述
        :param parameters: 策略参数
        :return: 策略实例
        """
        if strategy_type == "momentum":
            return MomentumStrategy(
                strategy_id=strategy_id,
                name=name or "动量策略",
                description=description or "基于价格动量的交易策略",
                parameters=parameters
            )
        elif strategy_type == "grid":
            return GridStrategy(
                strategy_id=strategy_id,
                name=name or "网格交易策略",
                description=description or "在价格区间内设置网格进行交易",
                parameters=parameters
            )
        elif strategy_type == "ma_cross":
            return MACrossStrategy(
                strategy_id=strategy_id,
                name=name or "均线交叉策略",
                description=description or "基于快慢均线交叉的交易策略",
                parameters=parameters
            )
        # 可以在这里添加更多策略类型
        else:
            raise ValueError(f"不支持的策略类型: {strategy_type}")
            
    @staticmethod
    def get_available_strategies():
        """获取所有可用的策略类型"""
        return [
            {
                "type": "momentum",
                "name": "动量策略",
                "description": "基于价格动量的交易策略",
                "default_parameters": {
                    "symbol": "BTC-USDT-SWAP",
                    "lookback_period": 5,
                    "threshold": 0.01,
                    "position_size_percent": 10  # 使用10%资金
                }
            },
            {
                "type": "grid",
                "name": "网格交易策略",
                "description": "在价格区间内设置网格进行交易",
                "default_parameters": {
                    "symbol": "BTC-USDT-SWAP",
                    "upper_price": 40000,
                    "lower_price": 30000,
                    "grid_num": 10,
                    "position_size_percent": 10  # 使用10%资金
                }
            },
            {
                "type": "ma_cross",
                "name": "均线交叉策略",
                "description": "基于快慢均线交叉的交易策略",
                "default_parameters": {
                    "symbol": "BTC-USDT-SWAP",
                    "fast_period": 5,
                    "slow_period": 20,
                    "position_size_percent": 10  # 使用10%资金
                }
            },
            {
                "type": "custom",
                "name": "自定义策略",
                "description": "通过直接编写Python代码实现的策略",
                "default_parameters": {
                    "symbol": "BTC-USDT-SWAP",
                    "code": "def execute_strategy(market_data, positions, account, parameters, logger):\n    # 在这里编写你的策略逻辑\n    return None",
                    "position_size_percent": 10  # 使用10%资金
                }
            }
        ]