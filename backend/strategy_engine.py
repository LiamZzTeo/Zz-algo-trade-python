import time
import asyncio
import logging
import traceback
from typing import Dict  # 添加这行导入
from okx_client import OKXClient  # 添加这行导入
from strategies.strategy_factory import StrategyFactory

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("StrategyEngine")

class StrategyEngine:
    def __init__(self, okx_client: OKXClient):
        self.okx_client = okx_client
        self.strategies = {}  # 存储所有策略
        self.market_data = {}  # 存储最新市场数据
        self.positions = []    # 存储当前持仓
        self.account_data = {} # 存储账户数据
        self.is_running = False
        self.update_interval = 0.5  # 数据更新间隔（秒）
        
    def register_strategy(self, strategy_type: str, strategy_id: str, name: str = None, 
                          description: str = None, parameters: Dict = None):
        """注册一个交易策略"""
        if strategy_id in self.strategies:
            logger.warning(f"策略 {strategy_id} 已存在，将被覆盖")
        
        try:
            # 使用策略工厂创建策略实例
            strategy = StrategyFactory.create_strategy(
                strategy_type=strategy_type,
                strategy_id=strategy_id,
                name=name,
                description=description,
                parameters=parameters
            )
            
            self.strategies[strategy_id] = {
                "instance": strategy,
                "enabled": False,
                "last_run": 0,
                "stats": {
                    "runs": 0,
                    "signals": 0,
                    "trades": 0
                }
            }
            
            logger.info(f"策略 {strategy_id} ({strategy_type}) 已注册")
            return strategy_id
            
        except Exception as e:
            logger.error(f"注册策略 {strategy_id} 失败: {str(e)}")
            raise
        
    def enable_strategy(self, strategy_id):
        """启用策略"""
        try:
            if strategy_id not in self.strategies:
                print(f"策略不存在: {strategy_id}")
                return False
                
            strategy_info = self.strategies[strategy_id]
            strategy_instance = strategy_info["instance"]
            
            # 检查策略参数是否有效
            if not self._validate_strategy_parameters(strategy_instance):
                print(f"策略参数无效: {strategy_id}")
                return False
                
            strategy_info["enabled"] = True
            logger.info(f"策略 {strategy_id} 已启用")
            return True
        except Exception as e:
            logger.error(f"启用策略 {strategy_id} 失败: {str(e)}")
            return False

    def _validate_strategy_parameters(self, strategy):
        """验证策略参数是否有效"""
        try:
            # 基本参数检查
            required_params = ["symbol"]
            for param in required_params:
                if param not in strategy.parameters:
                    print(f"缺少必要参数: {param}")
                    return False
                
            # 检查交易品种是否有效
            symbol = strategy.parameters.get("symbol")
            if not symbol:
                print("交易品种不能为空")
                return False
                
            return True
        except Exception as e:
            print(f"验证策略参数时出错: {str(e)}")
            return False
    
    def disable_strategy(self, strategy_id: str):
        """禁用策略"""
        if strategy_id in self.strategies:
            self.strategies[strategy_id]["enabled"] = False
            logger.info(f"策略 {strategy_id} 已禁用")
            return True
        logger.error(f"策略 {strategy_id} 不存在")
        return False
    
    async def update_market_data(self):
        """更新市场数据"""
        while self.is_running:
            try:
                # 获取账户数据
                account_data = self.okx_client.get_account_balance()
                if account_data.get("success", False):
                    self.account_data = account_data.get("data", {})
                
                # 获取持仓数据
                positions_data = self.okx_client.get_positions()
                if positions_data.get("success", False):
                    self.positions = positions_data.get("data", [])
                
                # 获取市场数据
                # 为每个策略获取相应的市场数据
                symbols = set()
                for strategy_info in self.strategies.values():
                    if strategy_info["enabled"]:
                        symbol = strategy_info["instance"].parameters.get("symbol")
                        if symbol:
                            symbols.add(symbol)
                
                for symbol in symbols:
                    market_data = await self.get_market_data(symbol)  # 使用异步方法
                    if market_data:
                        self.market_data[symbol] = market_data
                    else:
                        logger.warning(f"无法获取 {symbol} 的市场数据")
                
                logger.debug("市场数据已更新")
            except Exception as e:
                logger.error(f"更新市场数据错误: {str(e)}")
                traceback.print_exc()  # 添加堆栈跟踪以便调试
            
            await asyncio.sleep(self.update_interval)
    
    async def run_strategies(self):
        """运行所有启用的策略"""
        while self.is_running:
            current_time = time.time()
            
            for strategy_id, strategy_info in self.strategies.items():
                if not strategy_info["enabled"]:
                    continue
                    
                try:
                    strategy = strategy_info["instance"]
                    symbol = strategy.parameters.get("symbol")
                    
                    # 获取该策略需要的市场数据
                    market_data = await self.get_market_data(symbol)
                    
                    if not market_data:
                        logger.warning(f"策略 {strategy_id} - 无法获取市场数据")
                        continue
                    
                    # 执行策略
                    result = strategy.execute(
                        market_data=market_data,  # 直接传递整个market_data对象
                        positions=self.positions,
                        account=self.account_data
                    )
                    
                    # 处理策略结果
                    if result and "action" in result:
                        await self._execute_strategy_action(strategy_id, result)
                    
                    # 更新统计信息
                    strategy_info["last_run"] = current_time
                    strategy_info["stats"]["runs"] += 1
                    
                except Exception as e:
                    logger.error(f"执行策略 {strategy_id} 错误: {str(e)}")
                    traceback.print_exc()  # 添加堆栈跟踪以便调试
            
            await asyncio.sleep(1)  # 策略执行间隔
    
    async def _execute_strategy_action(self, strategy_id: str, action: Dict):
        """执行策略产生的交易动作"""
        try:
            action_type = action.get("action")
            
            if action_type == "buy":
                # 执行买入操作
                result = self.okx_client.place_order(
                    instId=action.get("symbol"),
                    tdMode="cross",
                    side="buy",
                    ordType="market",
                    sz=action.get("size")
                )
                
                if result.get("success", False):
                    logger.info(f"策略 {strategy_id} 买入信号执行成功: {action}")
                    self.strategies[strategy_id]["stats"]["trades"] += 1
                else:
                    logger.error(f"策略 {strategy_id} 买入信号执行失败: {result.get('msg', '')}")
                
            elif action_type == "sell":
                # 执行卖出操作
                result = self.okx_client.place_order(
                    instId=action.get("symbol"),
                    tdMode="cross",
                    side="sell",
                    ordType="market",
                    sz=action.get("size")
                )
                
                if result.get("success", False):
                    logger.info(f"策略 {strategy_id} 卖出信号执行成功: {action}")
                    self.strategies[strategy_id]["stats"]["trades"] += 1
                else:
                    logger.error(f"策略 {strategy_id} 卖出信号执行失败: {result.get('msg', '')}")
            
            self.strategies[strategy_id]["stats"]["signals"] += 1
            
        except Exception as e:
            logger.error(f"执行策略动作错误: {str(e)}")
    
    async def start(self):
        """启动策略引擎"""
        if self.is_running:
            logger.warning("策略引擎已在运行")
            return
            
        self.is_running = True
        logger.info("策略引擎启动")
        
        # 启动数据更新任务
        asyncio.create_task(self.update_market_data())
        
        # 启动策略执行任务
        asyncio.create_task(self.run_strategies())
    
    async def stop(self):
        """停止策略引擎"""
        self.is_running = False
        logger.info("策略引擎停止")
        
    def get_strategy_info(self, strategy_id):
        """获取策略信息"""
        if strategy_id not in self.strategies:
            return None
            
        strategy_info = self.strategies[strategy_id]
        strategy = strategy_info["instance"]
        
        return {
            "id": strategy_id,
            "type": strategy.__class__.__name__,
            "name": strategy.name,
            "description": strategy.description,
            "parameters": strategy.parameters,
            "enabled": strategy_info["enabled"],
            "last_run": strategy_info["last_run"],
            "stats": strategy_info["stats"]
        }
        
    def get_all_strategies(self):
        """获取所有策略信息"""
        result = []
        for strategy_id, strategy_info in self.strategies.items():
            strategy = strategy_info["instance"]
            result.append({
                "id": strategy_id,
                "type": strategy.__class__.__name__,
                "name": strategy.name,
                "description": strategy.description,
                "parameters": strategy.parameters,
                "enabled": strategy_info["enabled"],
                "last_run": strategy_info["last_run"],
                "stats": strategy_info["stats"]
            })
        return result
        
    def update_strategy_parameters(self, strategy_id, parameters):
        """更新策略参数"""
        if strategy_id not in self.strategies:
            logger.error(f"策略 {strategy_id} 不存在")
            return False
            
        try:
            strategy = self.strategies[strategy_id]["instance"]
            strategy.update_parameters(parameters)
            logger.info(f"策略 {strategy_id} 参数已更新")
            return True
        except Exception as e:
            logger.error(f"更新策略 {strategy_id} 参数失败: {str(e)}")


    async def run_strategy(self, strategy_id):
        """运行单个策略"""
        if strategy_id not in self.strategies:
            logger.warning(f"策略 {strategy_id} 不存在")
            return
            
        strategy_info = self.strategies[strategy_id]
        if not strategy_info["enabled"]:
            return
            
        try:
            # 获取市场数据
            symbol = strategy_info["instance"].parameters.get("symbol", "BTC-USDT-SWAP")
            market_data = await self.get_market_data(symbol)
            
            if not market_data:
                logger.warning(f"策略 {strategy_id} - 无法获取市场数据")
                return
                
            # 执行策略
            signal = strategy_info["instance"].execute(
                market_data=market_data,  # 直接传递整个market_data对象，不再使用["data"]
                positions=self.positions,
                account=self.account_data
            )
            
            # 更新策略统计信息
            strategy_info["last_run"] = int(time.time() * 1000)
            strategy_info["stats"]["runs"] += 1
            
            # 处理信号
            if signal:
                strategy_info["stats"]["signals"] += 1
                await self.process_signal(signal, strategy_id)
                
        except Exception as e:
            logger.error(f"执行策略 {strategy_id} 错误: {str(e)}")
            traceback.print_exc()

    async def get_market_data(self, symbol):
        """获取市场数据"""
        try:
            # 获取K线数据
            kline_data = self.okx_client.get_kline_data(symbol, "1m", 100)
            
            # 记录K线数据响应
            logger.debug(f"K线数据响应: {kline_data}")
            
            # 获取当前价格
            ticker_data = self.okx_client.get_ticker(symbol)
            
            # 记录Ticker数据响应
            logger.debug(f"Ticker数据响应: {ticker_data}")
            
            # 检查响应是否成功
            if not ticker_data.get("success", False) or not kline_data.get("success", False):
                logger.warning(f"获取市场数据失败: ticker_success={ticker_data.get('success')}, kline_success={kline_data.get('success')}")
                return None
            
            # 检查数据是否存在
            if not ticker_data.get("data") or not kline_data.get("data"):
                logger.warning(f"市场数据为空: ticker_data={bool(ticker_data.get('data'))}, kline_data={bool(kline_data.get('data'))}")
                return None
            
            # 检查数据长度
            if len(ticker_data["data"]) == 0 or len(kline_data["data"]) == 0:
                logger.warning(f"市场数据长度为0: ticker_length={len(ticker_data['data'])}, kline_length={len(kline_data['data'])}")
                return None
                
            # 构建市场数据对象
            market_data = {
                "symbol": symbol,
                "last": ticker_data["data"][0]["last"],
                "kline": kline_data["data"],
                "timestamp": int(time.time() * 1000)
            }
            
            return market_data
        except Exception as e:
            logger.error(f"获取市场数据时出错: {str(e)}")
            # 打印详细的异常堆栈
            traceback.print_exc()
            return None