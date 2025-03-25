from abc import ABC, abstractmethod
import logging

class BaseStrategy(ABC):
    """
    交易策略基类，所有策略都应继承此类
    """
    def __init__(self, strategy_id, name, description, parameters=None):
        self.strategy_id = strategy_id
        self.name = name
        self.description = description
        self.parameters = parameters or {}
        self.logger = logging.getLogger(f"strategy.{strategy_id}")
        
        # 确保position_size_percent参数存在
        if "position_size_percent" not in self.parameters:
            self.parameters["position_size_percent"] = 10  # 默认使用10%资金

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

    def calculate_position_size(self, account, current_price):
        """
        根据账户资金和百分比计算实际仓位大小
        
        Args:
            account: 账户信息
            current_price: 当前价格
        
        Returns:
            实际仓位大小
        """
        try:
            # 获取百分比参数
            percent = float(self.parameters.get("position_size_percent", 10))
            
            # 确保百分比在合理范围内
            percent = max(1, min(100, percent))
            
            # 获取可用资金
            available_balance = float(account.get("available", 0))
            if available_balance <= 0:
                self.logger.warning("可用资金不足")
                return 0
            
            # 计算可用资金的百分比
            amount = available_balance * (percent / 100)
            
            # 根据当前价格计算可买数量
            if current_price > 0:
                position_size = amount / current_price
                # 四舍五入到合适的精度
                position_size = round(position_size, 4)
                return position_size
            else:
                self.logger.warning("当前价格无效")
                return 0
        except Exception as e:
            self.logger.error(f"计算仓位大小错误: {str(e)}")
            return 0