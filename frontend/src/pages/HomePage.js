import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

function HomePage() {
  const [accountData, setAccountData] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const handleWebSocketData = (event) => {
      if (event.detail && event.detail.type === 'update' && event.detail.data) {
        setAccountData(event.detail.data.account);
        setLoading(false);
      }
    };
    
    window.addEventListener('wsData', handleWebSocketData);
    
    return () => {
      window.removeEventListener('wsData', handleWebSocketData);
    };
  }, []);

  return (
    <div className="dashboard-container">
      <div className="total-value-card">
        <h2>OKX 交易系统</h2>
        <p>实时监控您的交易账户</p>
        
        {loading ? (
          <div className="total-amount">加载中...</div>
        ) : accountData ? (
          <div className="total-amount">
            总资产: {accountData.totalEq || '0'}
          </div>
        ) : (
          <div className="total-amount">无法获取账户数据</div>
        )}
      </div>
      
      <div className="assets-grid">
        <div className="asset-card">
          <h4>账户信息</h4>
          <div className="asset-details">
            <p>查看您的账户余额和详细信息</p>
            <Link to="/account" className="nav-link">查看账户</Link>
          </div>
        </div>
        
        <div className="asset-card">
          <h4>持仓信息</h4>
          <div className="asset-details">
            <p>查看您当前的交易持仓</p>
            <Link to="/positions" className="nav-link">查看持仓</Link>
          </div>
        </div>
        
        {/* 移除了交易历史的卡片 */}
      </div>
    </div>
  );
}

export default HomePage;