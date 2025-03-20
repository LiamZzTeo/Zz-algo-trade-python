from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from okx_client import OKXClient
from strategy_engine import StrategyEngine
import asyncio
import json
import sys
import time
import os
from typing import List, Dict
from dotenv import load_dotenv
from pydantic import BaseModel

# 加载环境变量
load_dotenv()

app = FastAPI()
okx_client = OKXClient()
strategy_engine = StrategyEngine(okx_client)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局数据缓存
cache = {
    "account": {},
    "positions": [],
    "last_update": 0
}

# 数据更新间隔(秒)
UPDATE_INTERVAL = 0.5

# 策略模型
class StrategyConfig(BaseModel):
    strategy_id: str
    name: str
    description: str = ""
    parameters: Dict = {}
    enabled: bool = False

# 示例策略函数
def simple_ma_strategy(market_data, positions, account, config):
    """
    简单的移动平均线策略示例
    """
    if not market_data or "last" not in market_data:
        return None
        
    current_price = float(market_data["last"])
    fast_ma = config.get("fast_ma", 5)
    slow_ma = config.get("slow_ma", 20)
    
    # 这里应该有更复杂的逻辑来计算移动平均线
    # 简化示例，假设我们已经有了计算结果
    fast_ma_value = current_price * 0.99  # 模拟值
    slow_ma_value = current_price * 0.98  # 模拟值
    
    # 持仓检查
    has_position = False
    for pos in positions:
        if pos["instId"] == config.get("symbol") and float(pos["pos"]) > 0:
            has_position = True
            break
    
    # 策略逻辑
    if fast_ma_value > slow_ma_value and not has_position:
        # 生成买入信号
        return {
            "action": "buy",
            "symbol": config.get("symbol", "BTC-USDT-SWAP"),
            "size": config.get("position_size", "1"),
            "reason": "金叉信号"
        }
    elif fast_ma_value < slow_ma_value and has_position:
        # 生成卖出信号
        return {
            "action": "sell",
            "symbol": config.get("symbol", "BTC-USDT-SWAP"),
            "size": config.get("position_size", "1"),
            "reason": "死叉信号"
        }
    
    return None

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
    
    # 注册示例策略
    strategy_engine.register_strategy(
        "simple_ma",
        simple_ma_strategy,
        {
            "symbol": "BTC-USDT-SWAP",
            "fast_ma": 5,
            "slow_ma": 20,
            "position_size": "1"
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
    for strategy_id, strategy in strategy_engine.strategies.items():
        strategies_list.append({
            "id": strategy_id,
            "config": strategy["config"],
            "enabled": strategy["enabled"],
            "last_run": strategy["last_run"],
            "stats": strategy["stats"]
        })
    return {"success": True, "data": strategies_list}

@app.post("/api/strategies")
async def create_strategy(strategy: StrategyConfig):
    """创建新策略"""
    try:
        # 这里简化处理，实际应该根据策略类型选择不同的策略函数
        strategy_id = strategy_engine.register_strategy(
            strategy.strategy_id,
            simple_ma_strategy,  # 使用示例策略函数
            strategy.parameters
        )
        
        if strategy.enabled:
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
        # 更新策略配置
        strategy_engine.strategies[strategy_id]["config"] = strategy.parameters
        
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

@app.post("/api/strategies/{strategy_id}/enable")
async def enable_strategy(strategy_id: str):
    """启用策略"""
    if strategy_id not in strategy_engine.strategies:
        raise HTTPException(status_code=404, detail="策略不存在")
        
    result = strategy_engine.enable_strategy(strategy_id)
    return {"success": result}

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
