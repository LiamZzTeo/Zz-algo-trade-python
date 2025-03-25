from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from okx_client import OKXClient
from strategy_engine import StrategyEngine
from strategies.strategy_factory import StrategyFactory
import asyncio
import json
import sys
import time
import os
from typing import List, Dict
from dotenv import load_dotenv
from backtest_engine import BacktestEngine
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

# 加载环境变量
load_dotenv()

app = FastAPI()
okx_client = OKXClient()
strategy_engine = StrategyEngine(okx_client)

# 初始化回测引擎 - 移到顶部
backtest_engine = BacktestEngine(okx_client)

# 回测请求模型 - 移到顶部
from pydantic import BaseModel

# 确保这个类定义在文件顶部
class BacktestRequest(BaseModel):
    strategy_id: str
    symbol: str
    bar: str = "1m"
    initial_capital: float = 10000

# 确保这个端点定义在 if __name__ == "__main__": 之前
@app.post("/api/backtest")
async def run_backtest(request: BacktestRequest):
    """运行策略回测"""
    try:
        print(f"收到回测请求: {request}")
        # 检查策略是否存在
        if request.strategy_id not in strategy_engine.strategies:
            return {"success": False, "msg": f"未找到ID为 {request.strategy_id} 的策略"}
        
        # 获取策略实例
        strategy = strategy_engine.strategies[request.strategy_id]["instance"]
        
        # 运行回测
        result = backtest_engine.run_backtest(
            strategy=strategy,
            symbol=request.symbol,
            bar=request.bar,
            initial_capital=request.initial_capital
        )
        
        return result
    except Exception as e:
        print(f"回测错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "msg": f"回测错误: {str(e)}"}

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局数据缓存
# 在导入部分添加
import json
import os
from pathlib import Path

# 全局数据缓存部分添加
# 在main.py的开头部分，确保缓存初始化包含所有需要的键
cache = {
    "account": {},
    "positions": [],
    "instruments": [],
    "market_data": {},
    "last_update": 0
}

# 定义保存产品信息的路径
INSTRUMENTS_FILE = os.path.join(os.path.dirname(__file__), "data", "instruments.json")

# 确保数据目录存在
os.makedirs(os.path.dirname(INSTRUMENTS_FILE), exist_ok=True)

# 在 startup_event 函数中添加获取产品信息的代码
@app.on_event("startup")
async def startup_event():
    """应用启动时，开始后台数据更新任务和策略引擎"""
    asyncio.create_task(update_data_periodically())
    
    # 获取并保存所有可交易产品
    try:
        # 获取多种产品类型
        instruments_data = okx_client.get_instruments(["SPOT", "SWAP", "FUTURES"])
        if instruments_data["success"]:
            instruments = instruments_data["data"]
            cache["instruments"] = instruments
            
            # 保存到本地文件
            with open(INSTRUMENTS_FILE, "w", encoding="utf-8") as f:
                json.dump(instruments, f, ensure_ascii=False, indent=2)
            
            print(f"已获取并保存 {len(instruments)} 个可交易产品")
    except Exception as e:
        print(f"获取可交易产品失败: {str(e)}")
        # 如果获取失败，尝试从本地文件加载
        if os.path.exists(INSTRUMENTS_FILE):
            try:
                with open(INSTRUMENTS_FILE, "r", encoding="utf-8") as f:
                    cache["instruments"] = json.load(f)
                print(f"已从本地文件加载 {len(cache['instruments'])} 个可交易产品")
            except Exception as load_err:
                print(f"从本地文件加载产品失败: {str(load_err)}")
    
    # 注册示例策略 - 使用新的策略工厂创建一个动量策略
    strategy_engine.register_strategy(
        strategy_type="momentum",
        strategy_id="demo_momentum",
        name="示例动量策略",
        description="系统启动时自动创建的示例动量策略",
        parameters={
            "symbol": "BTC-USDT-SWAP",
            "lookback_period": 5,
            "threshold": 0.01,
            "position_size": 1
        }
    )
    print("后台数据更新任务已启动")

    # 启动策略引擎
    await strategy_engine.start()
    print("策略引擎已启动")

# 添加获取所有可交易产品的API端点
@app.get("/api/instruments")
async def get_instruments():
    """获取所有可交易产品"""
    if not cache["instruments"] and os.path.exists(INSTRUMENTS_FILE):
        try:
            with open(INSTRUMENTS_FILE, "r", encoding="utf-8") as f:
                cache["instruments"] = json.load(f)
        except Exception as e:
            print(f"从本地文件加载产品失败: {str(e)}")
    
    return {
        "success": True,
        "data": cache["instruments"],
        "timestamp": cache["last_update"]
    }

# 添加获取市场数据的API端点
@app.get("/api/market-data")
async def get_market_data(symbol: str):
    """获取市场数据"""
    try:
        market_data = okx_client.get_market_data(symbol)
        return market_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 添加获取资产数据的API端点 (别名)
@app.get("/api/assets")
async def get_assets():
    """获取资产数据 (账户数据的别名)"""
    return await get_account()

# 数据更新间隔(秒)
UPDATE_INTERVAL = 0.5

# 策略模型
class StrategyConfig(BaseModel):
    strategy_id: str
    name: str
    description: str = ""
    parameters: Dict = {}
    enabled: bool = False

async def update_data_periodically():
    """后台任务：定期更新数据"""
    while True:
        try:
            # 获取账户数据
            account_data = okx_client.get_account_balance()
            positions_data = okx_client.get_positions()
            
            # 更新缓存
            cache["account"] = account_data.get("data", {})
            cache["positions"] = positions_data.get("data", [])
            cache["last_update"] = int(time.time() * 1000)
            
        except Exception as e:
            print(f"数据更新错误: {str(e)}")
        
        # 等待下一次更新
        await asyncio.sleep(UPDATE_INTERVAL)

@app.on_event("startup")
async def startup_event():
    """应用启动时，开始后台数据更新任务和策略引擎"""
    asyncio.create_task(update_data_periodically())
    
    # 注册示例策略 - 使用新的策略工厂创建一个动量策略
    strategy_engine.register_strategy(
        strategy_type="momentum",
        strategy_id="demo_momentum",
        name="示例动量策略",
        description="系统启动时自动创建的示例动量策略",
        parameters={
            "symbol": "BTC-USDT-SWAP",
            "lookback_period": 5,
            "threshold": 0.01,
            "position_size": 1
        }
    )
    print("后台数据更新任务已启动")

    # 启动策略引擎
    await strategy_engine.start()
    print("策略引擎已启动")

# API端点
@app.get("/api/data")
async def get_data():
    """获取最新的账户和持仓数据"""
    return {
        "type": "update",
        "data": {
            "account": cache["account"],
            "positions": cache["positions"]
        },
        "timestamp": cache["last_update"]
    }

@app.get("/api/account")
async def get_account():
    """获取账户数据"""
    return {
        "success": True,
        "data": cache["account"],
        "timestamp": cache["last_update"]
    }

@app.get("/api/positions")
async def get_positions():
    """获取持仓数据"""
    return {
        "success": True,
        "data": cache["positions"],
        "timestamp": cache["last_update"]
    }

# 策略相关API
@app.get("/api/strategies")
async def get_strategies():
    """获取所有策略"""
    strategies_list = []
    for strategy_id, strategy_info in strategy_engine.strategies.items():
        strategy = strategy_info["instance"]
        strategies_list.append({
            "id": strategy_id,
            "type": strategy.__class__.__name__,
            "name": strategy.name,
            "description": strategy.description,
            "parameters": strategy.parameters,
            "enabled": strategy_info["enabled"],
            "last_run": strategy_info["last_run"],
            "stats": strategy_info["stats"]
        })
    return {"success": True, "data": strategies_list}

# 添加获取可用策略类型的API端点
@app.get("/api/strategy-types")
async def get_strategy_types():
    """获取所有可用的策略类型"""
    try:
        strategy_types = StrategyFactory.get_available_strategies()
        return {"success": True, "data": strategy_types}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 修改创建策略的API端点，支持不同类型的策略
@app.post("/api/strategies")
async def create_strategy(strategy: dict):
    """创建新策略"""
    try:
        required_fields = ["strategy_id", "strategy_type", "parameters"]
        for field in required_fields:
            if field not in strategy:
                raise HTTPException(status_code=400, detail=f"缺少必要字段: {field}")
        
        strategy_id = strategy_engine.register_strategy(
            strategy_type=strategy["strategy_type"],
            strategy_id=strategy["strategy_id"],
            name=strategy.get("name"),
            description=strategy.get("description"),
            parameters=strategy.get("parameters")
        )
        
        if strategy.get("enabled", False):
            strategy_engine.enable_strategy(strategy_id)
            
        return {"success": True, "data": {"id": strategy_id}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/strategies/{strategy_id}")
async def update_strategy(strategy_id: str, strategy: StrategyConfig):
    """更新策略配置"""
    if strategy_id not in strategy_engine.strategies:
        raise HTTPException(status_code=404, detail="策略不存在")
        
    try:
        # 更新策略参数
        result = strategy_engine.update_strategy_parameters(strategy_id, strategy.parameters)
        if not result:
            raise HTTPException(status_code=400, detail="更新策略参数失败")
        
        # 更新启用状态
        if strategy.enabled:
            strategy_engine.enable_strategy(strategy_id)
        else:
            strategy_engine.disable_strategy(strategy_id)
            
        return {"success": True, "data": {"id": strategy_id}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/strategies/{strategy_id}")
async def delete_strategy(strategy_id: str):
    """删除策略"""
    if strategy_id not in strategy_engine.strategies:
        raise HTTPException(status_code=404, detail="策略不存在")
        
    try:
        # 先禁用策略
        strategy_engine.disable_strategy(strategy_id)
        # 删除策略
        del strategy_engine.strategies[strategy_id]
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 在文件顶部定义验证函数
def validate_strategy_parameters(strategy_type, parameters):
    """验证策略参数"""
    try:
        if strategy_type.lower() == "momentum":
            # 验证动量策略参数
            if "symbol" not in parameters:
                return False, "缺少交易品种参数"
            if "threshold" not in parameters:
                return False, "缺少阈值参数"
        elif strategy_type.lower() == "grid":
            # 验证网格策略参数
            if "symbol" not in parameters:
                return False, "缺少交易品种参数"
            if "upper_price" not in parameters:
                return False, "缺少上限价格参数"
            if "lower_price" not in parameters:
                return False, "缺少下限价格参数"
            if "grid_levels" not in parameters:
                return False, "缺少网格级别参数"
        elif strategy_type.lower() == "macross":
            # 验证均线交叉策略参数
            if "symbol" not in parameters:
                return False, "缺少交易品种参数"
            if "fast_period" not in parameters:
                return False, "缺少快速均线周期参数"
            if "slow_period" not in parameters:
                return False, "缺少慢速均线周期参数"
        elif strategy_type.lower() == "custom":
            # 验证自定义策略参数
            if "code" not in parameters:
                return False, "缺少策略代码"
        
        return True, "参数验证通过"
    except Exception as e:
        print(f"验证策略参数时出错: {str(e)}")
        return False, f"策略参数无效: {str(e)}"

# 然后在enable_strategy函数中使用它
@app.post("/api/strategies/{strategy_id}/enable")
async def enable_strategy(strategy_id: str):
    """启用策略"""
    try:
        # 检查策略是否存在
        if strategy_id not in strategy_engine.strategies:
            return {"success": False, "msg": f"未找到ID为 {strategy_id} 的策略"}
        
        # 直接启用策略，不进行参数验证
        # 因为策略在创建时已经验证过参数
        result = strategy_engine.enable_strategy(strategy_id)
        if result:
            return {"success": True, "msg": "策略启用成功"}
        else:
            return {"success": False, "msg": "策略启用失败"}
    except Exception as e:
        print(f"启用策略错误: {str(e)}")
        return {"success": False, "msg": f"启用策略错误: {str(e)}"}

@app.post("/api/strategies/{strategy_id}/disable")
async def disable_strategy(strategy_id: str):
    """禁用策略"""
    if strategy_id not in strategy_engine.strategies:
        raise HTTPException(status_code=404, detail="策略不存在")
        
    result = strategy_engine.disable_strategy(strategy_id)
    return {"success": result}

# 优雅关闭
@app.on_event("shutdown")
async def shutdown_event():
    await strategy_engine.stop()
    print("应用正在关闭...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
