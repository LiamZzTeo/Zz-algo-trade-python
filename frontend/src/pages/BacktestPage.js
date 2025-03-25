// 回测表单提交函数
const handleSubmit = async (values) => {
  setLoading(true);
  try {
    const { strategy_id, start_time, end_time, symbol, timeframe, initial_balance } = values;
    
    // 打印调试信息
    console.log("回测参数:", values);
    
    const response = await fetch('http://localhost:8000/api/backtest', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        strategy_id,
        start_time,
        end_time,
        symbol,
        timeframe,
        initial_balance
      }),
    });

    const data = await response.json();
    
    if (data.success) {
      message.success('回测完成');
      // 导航到回测结果页面
      navigate(`/backtest-result/${data.backtest_id}`);
    } else {
      message.error(data.msg || '回测失败');
    }
  } catch (error) {
    console.error('回测错误:', error);
    message.error('回测请求失败');
  } finally {
    setLoading(false);
  }
};