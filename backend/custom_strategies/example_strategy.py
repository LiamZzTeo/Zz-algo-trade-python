def execute_strategy(market_data, positions, account, parameters, logger):
    """
    自定义策略执行函数
    
    参数:
    - market_data: 市场数据，包含symbol, last, kline等
    - positions: 持仓数据列表
    - account: 账户数据
    - parameters: 策略参数
    - logger: 日志记录器
    
    返回:
    - 交易信号字典或None
    """
    # 检查是否有市场数据
    if not market_data or "last" not in market_data:
        logger.warning("无法获取市场数据")
        return None
        
    # 获取当前价格
    current_price = float(market_data["last"])
    symbol = parameters.get("symbol", "BTC-USDT-SWAP")
    position_size = parameters.get("position_size", 1)
    
    # 检查是否有持仓
    has_position = False
    for position in positions:
        if position.get("instId") == symbol and float(position.get("pos", 0)) > 0:
            has_position = True
            break
    
    # 简单策略逻辑：价格超过40000买入，低于35000卖出
    if current_price > 40000 and not has_position:
        logger.info(f"价格 {current_price} 超过40000，生成买入信号")
        return {
            "action": "buy",
            "symbol": symbol,
            "size": str(position_size),
            "reason": f"价格 {current_price} 超过40000"
        }
    elif current_price < 35000 and has_position:
        logger.info(f"价格 {current_price} 低于35000，生成卖出信号")
        return {
            "action": "sell",
            "symbol": symbol,
            "size": str(position_size),
            "reason": f"价格 {current_price} 低于35000"
        }
    
    return None