from .base_strategy import BaseStrategy
import time

class GridStrategy(BaseStrategy):
    """
    网格交易策略：在价格区间内设置网格，价格上涨卖出，价格下跌买入
    
    参数:
    - symbol: 交易品种
    - upper_price: 网格上限价格
    - lower_price: 网格下限价格
    - grid_num: 网格数量
    - position_size: 每格仓位大小
    """
    
    def __init__(self, strategy_id, name="网格交易策略", description="在价格区间内设置网格进行交易", parameters=None):
        default_params = {
            "symbol": "BTC-USDT-SWAP",
            "upper_price": 40000,
            "lower_price": 30000,
            "grid_num": 10,
            "position_size": 0.01
        }
        
        if parameters:
            default_params.update(parameters)
            
        super().__init__(strategy_id, name, description, default_params)
        
        # 初始化网格
        self._init_grid()
        self.last_price = None
        self.last_signal_time = 0
        self.signal_cooldown = 30  # 信号冷却时间（秒）
        
    def _init_grid(self):
        """初始化价格网格"""
        upper = float(self.parameters["upper_price"])
        lower = float(self.parameters["lower_price"])
        num = int(self.parameters["grid_num"])
        
        if upper <= lower or num <= 0:
            self.logger.error("网格参数无效")
            self.grid_prices = []
            return
            
        # 计算网格价格点
        step = (upper - lower) / num
        self.grid_prices = [lower + i * step for i in range(num + 1)]
        self.logger.info(f"网格初始化完成，共 {len(self.grid_prices)} 个价格点")
        
    def update_parameters(self, parameters):
        """更新策略参数"""
        super().update_parameters(parameters)
        # 重新初始化网格
        self._init_grid()
        
    def execute(self, market_data, positions, account):
        """执行策略逻辑"""
        # 检查是否有市场数据
        if not market_data or "last" not in market_data:
            self.logger.warning("无法获取市场数据")
            return None
            
        # 获取当前价格
        current_price = float(market_data["last"])
        current_time = time.time()
        
        # 如果是首次执行，记录价格并返回
        if self.last_price is None:
            self.last_price = current_price
            return None
            
        # 信号冷却检查
        if current_time - self.last_signal_time < self.signal_cooldown:
            return None
            
        # 检查价格是否穿过网格线
        for grid_price in self.grid_prices:
            # 价格上穿网格线，卖出信号
            if self.last_price < grid_price <= current_price:
                self.last_price = current_price
                self.last_signal_time = current_time
                self.logger.info(f"价格上穿网格线 {grid_price}，生成卖出信号")
                
                return {
                    "action": "sell",
                    "symbol": self.parameters["symbol"],
                    "size": str(self.parameters["position_size"]),
                    "reason": f"价格上穿网格线 {grid_price}"
                }
                
            # 价格下穿网格线，买入信号
            elif self.last_price > grid_price >= current_price:
                self.last_price = current_price
                self.last_signal_time = current_time
                self.logger.info(f"价格下穿网格线 {grid_price}，生成买入信号")
                
                return {
                    "action": "buy",
                    "symbol": self.parameters["symbol"],
                    "size": str(self.parameters["position_size"]),
                    "reason": f"价格下穿网格线 {grid_price}"
                }
                
        # 更新最新价格
        self.last_price = current_price
        return None