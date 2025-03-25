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
            "position_size_percent": 10  # 默认使用10%资金
        }
        
        if parameters:
            default_params.update(parameters)
            
        super().__init__(strategy_id, name, description, default_params)
        self.last_signal_time = 0
        self.signal_cooldown = 30  # 信号冷却时间（秒）
        # 移除对不存在方法的调用
        # self.grid_levels = self._calculate_grid_levels()
        
        # 初始化网格
        self._init_grid()
        self.last_price = None
        self.last_signal_time = 0
        self.signal_cooldown = 30  # 信号冷却时间（秒）
        
    # 添加_calculate_grid_levels方法
    def _calculate_grid_levels(self):
        """计算网格价格水平"""
        try:
            upper_price = float(self.parameters.get("upper_price", 40000))
            lower_price = float(self.parameters.get("lower_price", 30000))
            grid_num = int(self.parameters.get("grid_num", 10))
            
            if upper_price <= lower_price or grid_num <= 0:
                self.logger.error("网格参数无效")
                return []
                
            # 计算网格价格点
            step = (upper_price - lower_price) / grid_num
            grid_levels = [lower_price + i * step for i in range(grid_num + 1)]
            
            self.logger.info(f"网格水平计算完成，共 {len(grid_levels)} 个价格点")
            return grid_levels
        except Exception as e:
            self.logger.error(f"计算网格水平错误: {str(e)}")
            return []
        
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
            upper_price = float(self.parameters.get("upper_price", 40000))
            lower_price = float(self.parameters.get("lower_price", 30000))
            grid_num = int(self.parameters.get("grid_num", 10))
            
            # 计算实际仓位大小
            position_size = self.calculate_position_size(account, current_price)
            
            # 计算网格价格
            grid_step = (upper_price - lower_price) / grid_num
            grid_prices = [lower_price + i * grid_step for i in range(grid_num + 1)]
            
            # 检查当前价格在哪个网格区间
            current_grid = None
            for i in range(len(grid_prices) - 1):
                if grid_prices[i] <= current_price < grid_prices[i + 1]:
                    current_grid = i
                    break
            
            if current_grid is None:
                # 价格超出网格范围
                return None
            
            # 检查是否有持仓
            has_position = False
            position_side = None
            for position in positions:
                pos_symbol = position.get("symbol", position.get("instId", ""))
                if pos_symbol == symbol:
                    has_position = True
                    position_side = position.get("side", "long" if float(position.get("pos", 0)) > 0 else "short")
                    break
            
            # 网格交易逻辑
            # 如果价格接近下一个网格线，考虑买入
            if current_price < grid_prices[current_grid + 1] * 1.01 and not has_position:
                signal = {
                    "action": "buy",
                    "symbol": symbol,
                    "size": position_size,
                    "reason": f"网格买入信号: 价格 {current_price} 接近网格线 {grid_prices[current_grid + 1]}"
                }
                
                # 添加K线周期信息
                if timeframe:
                    signal["timeframe"] = timeframe
                    
                return signal
            
            # 如果价格接近当前网格线，考虑卖出
            if current_price > grid_prices[current_grid] * 0.99 and has_position and position_side == "long":
                signal = {
                    "action": "sell",
                    "symbol": symbol,
                    "size": position_size,
                    "reason": f"网格卖出信号: 价格 {current_price} 接近网格线 {grid_prices[current_grid]}"
                }
                
                # 添加K线周期信息
                if timeframe:
                    signal["timeframe"] = timeframe
                    
                return signal
            
            return None
        except Exception as e:
            self.logger.error(f"生成网格交易信号错误: {str(e)}")
            return None

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
                
                signal = {
                    "action": "sell",
                    "symbol": symbol,
                    "size": position_size,
                    "reason": f"价格上穿网格线 {grid_price}"
                }
                
                # 添加K线周期信息
                if timeframe:
                    signal["timeframe"] = timeframe
                    
                return signal
                
            # 价格下穿网格线，买入信号
            elif self.last_price > grid_price >= current_price:
                self.last_price = current_price
                self.last_signal_time = current_time
                self.logger.info(f"价格下穿网格线 {grid_price}，生成买入信号")
                
                signal = {
                    "action": "buy",
                    "symbol": symbol,
                    "size": position_size,
                    "reason": f"价格下穿网格线 {grid_price}"
                }
                
                # 添加K线周期信息
                if timeframe:
                    signal["timeframe"] = timeframe
                    
                return signal
                
        # 更新最新价格
        self.last_price = current_price
        return None