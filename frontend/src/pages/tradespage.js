import React, { useState, useEffect } from 'react';

function TradesPage() {
  const [tradeHistory, setTradeHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const handleWebSocketData = (event) => {
      if (event.detail && event.detail.type === 'update' && event.detail.data.trades) {
        setTradeHistory(event.detail.data.trades);
        setLoading(false);
      }
    };
    
    window.addEventListener('wsData', handleWebSocketData);
    
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
      window.removeEventListener('wsData', handleWebSocketData);
    };
  }, []);

  if (loading) {
    return <div className="loading-container">
      <div className="loading-spinner"></div>
      <div className="loading-text">加载交易历史中...</div>
    </div>;
  }

  if (error) {
    return <div className="error-container">
      <h2 className="page-header">交易历史</h2>
      <div className="error-message">错误: {error}</div>
    </div>;
  }

  if (!tradeHistory || tradeHistory.length === 0) {
    return <div className="page-container">
      <h2 className="page-header">交易历史</h2>
      <div className="empty-state">
        <div className="empty-icon">📊</div>
        <div className="empty-text">暂无交易记录</div>
      </div>
    </div>;
  }

  return (
    <div className="page-container">
      <h2 className="page-header">交易历史</h2>
      
      <div className="trade-history">
        <table className="trade-table">
          <thead>
            <tr>
              <th>订单ID</th>
              <th>交易对</th>
              <th>方向</th>
              <th>价格</th>
              <th>数量</th>
              <th>时间</th>
            </tr>
          </thead>
          <tbody>
            {tradeHistory.map((trade, index) => (
              <tr key={trade.ordId || index} className={trade.side === 'buy' ? 'buy-row' : 'sell-row'}>
                <td>{trade.ordId}</td>
                <td>{trade.instId}</td>
                <td className={trade.side === 'buy' ? 'buy-side' : 'sell-side'}>
                  {trade.side === 'buy' ? '买入' : '卖出'}
                </td>
                <td>{trade.px}</td>
                <td>{trade.sz}</td>
                <td>{new Date(parseInt(trade.cTime)).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default TradesPage;