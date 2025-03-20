import React, { useState, useEffect } from 'react';

function TradesPage() {
  const [tradeHistory, setTradeHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // 修改事件名称从wsData为apiData
    const handleApiData = (event) => {
      if (event.detail && event.detail.type === 'update' && event.detail.data.trades) {
        setTradeHistory(event.detail.data.trades);
        setLoading(false);
      }
    };
    
    window.addEventListener('apiData', handleApiData);
    
    // 初始加载时尝试从API获取数据
    const fetchTradeHistory = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/trade/orders-history');
        if (!response.ok) {
          throw new Error(`HTTP错误: ${response.status}`);
        }
        const data = await response.json();
        if (data.success && data.data) {
          setTradeHistory(data.data);
        } else {
          setError(data.msg || '获取交易历史失败');
        }
      } catch (error) {
        console.error('获取交易历史错误:', error);
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchTradeHistory();
    
    return () => {
      window.removeEventListener('apiData', handleApiData);
    };
  }, []);

  if (loading) {
    return <div className="loading">加载交易历史中...</div>;
  }

  if (error) {
    return <div className="error">错误: {error}</div>;
  }

  return (
    <div className="page-container">
      <h2 className="page-header">交易历史</h2>
      
      {tradeHistory && tradeHistory.length > 0 ? (
        <div className="trades-table-container">
          <table className="trades-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>合约</th>
                <th>方向</th>
                <th>价格</th>
                <th>数量</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              {tradeHistory.map((trade, index) => (
                <tr key={index}>
                  <td>{new Date(trade.cTime).toLocaleString()}</td>
                  <td>{trade.instId}</td>
                  <td className={trade.side === 'buy' ? 'buy-side' : 'sell-side'}>
                    {trade.side === 'buy' ? '买入' : '卖出'}
                  </td>
                  <td>{trade.avgPx || trade.px}</td>
                  <td>{trade.sz}</td>
                  <td>{trade.state === 'filled' ? '已成交' : trade.state}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="no-trades">
          <p>暂无交易历史</p>
        </div>
      )}
    </div>
  );
}

export default TradesPage;