@router.post("/backtest")
async def run_backtest(request: Request):
    try:
        data = await request.json()
        strategy_id = data.get("strategy_id")
        start_time = data.get("start_time")
        end_time = data.get("end_time")
        symbol = data.get("symbol")
        timeframe = data.get("timeframe")
        initial_balance = data.get("initial_balance", 10000)
        
        # 打印详细的调试信息
        print(f"收到回测请求 - 策略ID: {strategy_id}")
        print(f"回测参数 - 交易品种: {symbol}, K线周期: {timeframe}")
        print(f"回测参数 - 开始时间: {start_time}, 结束时间: {end_time}")
        print(f"回测参数 - 初始资金: {initial_balance}")
        
        if not all([strategy_id, start_time, end_time, symbol, timeframe]):
            missing = []
            if not strategy_id: missing.append("strategy_id")
            if not start_time: missing.append("start_time")
            if not end_time: missing.append("end_time")
            if not symbol: missing.append("symbol")
            if not timeframe: missing.append("timeframe")
            return {"success": False, "msg": f"缺少必要参数: {', '.join(missing)}"}
            
        result = backtest_service.run_backtest(
            strategy_id, 
            start_time, 
            end_time, 
            symbol, 
            timeframe, 
            initial_balance
        )
        
        # 打印回测结果概览
        if result.get("success"):
            overview = result.get("result", {}).get("overview", {})
            print(f"回测完成 - 交易品种: {overview.get('symbol')}, K线周期: {overview.get('timeframe')}")
            print(f"回测结果 - 初始资金: {overview.get('initial_balance')}, 最终资金: {overview.get('final_balance')}")
        
        return result
    except Exception as e:
        logger.error(f"回测API错误: {str(e)}")
        return {"success": False, "msg": f"回测失败: {str(e)}"}