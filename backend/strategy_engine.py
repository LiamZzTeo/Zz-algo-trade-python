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
        
    def enable_strategy(self, strategy_id: str):
        """启用策略"""
        if strategy_id in self.strategies:
            self.strategies[strategy_id]["enabled"] = True
            logger.info(f"策略 {strategy_id} 已启用")
            return True
        logger.error(f"策略 {strategy_id} 不存在")
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
                    market_data = self.okx_client.get_market_data(symbol)
                    if market_data.get("success", False):
                        self.market_data[symbol] = market_data.get("data", {})
                
                logger.debug("市场数据已更新")
            except Exception as e:
                logger.error(f"更新市场数据错误: {str(e)}")
            
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
                    market_data = self.market_data.get(symbol, {})
                    
                    # 执行策略
                    result = strategy.execute(
                        market_data=market_data,
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
                market_data=market_data["data"],
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
            
            # 获取当前价格
            ticker_data = self.okx_client.get_ticker(symbol)
            
            if not ticker_data.get("data") or not kline_data.get("data"):
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
            return None