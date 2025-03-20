import time
import asyncio
import logging
from typing import Dict, List, Any, Callable
from okx_client import OKXClient

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
        
    def register_strategy(self, strategy_id: str, strategy_func: Callable, config: Dict = None):
        """注册一个交易策略"""
        if strategy_id in self.strategies:
            logger.warning(f"策略 {strategy_id} 已存在，将被覆盖")
            
        self.strategies[strategy_id] = {
            "function": strategy_func,
            "config": config or {},
            "enabled": False,
            "last_run": 0,
            "stats": {
                "runs": 0,
                "signals": 0,
                "trades": 0
            }
        }
        logger.info(f"策略 {strategy_id} 已注册")
        return strategy_id
        
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
                if account_data["success"]:
                    self.account_data = account_data["data"]
                
                # 获取持仓数据
                positions_data = self.okx_client.get_positions()
                if positions_data["success"]:
                    self.positions = positions_data["data"]
                
                # 获取市场数据（这里可以添加获取K线、深度等数据）
                # 例如：获取BTC永续合约的最新行情
                market_data = self.okx_client.get_market_data("BTC-USDT-SWAP")
                if market_data["success"]:
                    self.market_data = market_data["data"]
                
                logger.debug("市场数据已更新")
            except Exception as e:
                logger.error(f"更新市场数据错误: {str(e)}")
            
            await asyncio.sleep(self.update_interval)
    
    async def run_strategies(self):
        """运行所有启用的策略"""
        while self.is_running:
            current_time = time.time()
            
            for strategy_id, strategy in self.strategies.items():
                if not strategy["enabled"]:
                    continue
                    
                try:
                    # 执行策略函数
                    result = strategy["function"](
                        market_data=self.market_data,
                        positions=self.positions,
                        account=self.account_data,
                        config=strategy["config"]
                    )
                    
                    # 处理策略结果
                    if result and "action" in result:
                        await self._execute_strategy_action(strategy_id, result)
                    
                    # 更新统计信息
                    strategy["last_run"] = current_time
                    strategy["stats"]["runs"] += 1
                    
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
                    tdMode=action.get("tdMode", "cross"),
                    side="buy",
                    ordType=action.get("ordType", "market"),
                    sz=action.get("size"),
                    px=action.get("price")
                )
                
                if result["success"]:
                    logger.info(f"策略 {strategy_id} 买入信号执行成功: {action}")
                    self.strategies[strategy_id]["stats"]["trades"] += 1
                else:
                    logger.error(f"策略 {strategy_id} 买入信号执行失败: {result['msg']}")
                
            elif action_type == "sell":
                # 执行卖出操作
                result = self.okx_client.place_order(
                    instId=action.get("symbol"),
                    tdMode=action.get("tdMode", "cross"),
                    side="sell",
                    ordType=action.get("ordType", "market"),
                    sz=action.get("size"),
                    px=action.get("price")
                )
                
                if result["success"]:
                    logger.info(f"策略 {strategy_id} 卖出信号执行成功: {action}")
                    self.strategies[strategy_id]["stats"]["trades"] += 1
                else:
                    logger.error(f"策略 {strategy_id} 卖出信号执行失败: {result['msg']}")
            
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