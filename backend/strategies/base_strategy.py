from abc import ABC, abstractmethod
import logging

class BaseStrategy(ABC):
    """
    交易策略基类，所有策略都应继承此类
    """
    def __init__(self, strategy_id, name, description="", parameters=None):
        self.strategy_id = strategy_id
        self.name = name
        self.description = description
        self.parameters = parameters or {}
        self.logger = logging.getLogger(f"Strategy.{strategy_id}")
        
    def run(self, market_data, positions, account):
        """
        运行策略
        
        :param market_data: 市场数据
        :param positions: 持仓数据
        :param account: 账户数据
        :return: 交易信号或None
        """
        if not market_data:
            return None
            
        # 调用子类实现的策略逻辑
        return self.generate_signal(market_data, positions, account)
        
    @abstractmethod
    def generate_signal(self, market_data, positions, account):
        """
        生成交易信号，子类必须实现此方法
        
        :param market_data: 市场数据
        :param positions: 持仓数据
        :param account: 账户数据
        :return: 交易信号或None
        """
        pass
    
    def update_parameters(self, parameters):
        """更新策略参数"""
        self.parameters.update(parameters)
        self.logger.info(f"策略参数已更新: {parameters}")
        
    def get_info(self):
        """获取策略信息"""
        return {
            "id": self.strategy_id,
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }