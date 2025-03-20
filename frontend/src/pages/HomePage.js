import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

function HomePage() {
  const [accountData, setAccountData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);
  
  useEffect(() => {
    console.log('HomePage组件已挂载');
    
    // 处理API数据更新事件
    const handleApiData = (event) => {
      if (event.detail && event.detail.type === 'update' && event.detail.data) {
        console.log('收到新数据更新:', new Date().toLocaleTimeString());
        setAccountData(event.detail.data.account);
        setLastUpdate(new Date().toLocaleTimeString());
        setLoading(false);
      }
    };
    
    window.addEventListener('apiData', handleApiData);
    
    // 初始加载时尝试从API获取数据
    const fetchInitialData = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/account');
        if (!response.ok) {
          throw new Error(`HTTP错误: ${response.status}`);
        }
        const data = await response.json();
        if (data.success) {
          setAccountData(data.data);
          setLastUpdate(new Date().toLocaleTimeString());
          setLoading(false);
        }
      } catch (error) {
        console.error('获取初始数据失败:', error);
      }
    };
    
    fetchInitialData();
    
    // 设置一个定时器，每秒检查一次组件是否仍在接收更新
    const checkUpdateTimer = setInterval(() => {
      const now = new Date();
      const lastUpdateTime = lastUpdate ? new Date(`${new Date().toDateString()} ${lastUpdate}`) : null;
      
      if (lastUpdateTime && (now - lastUpdateTime) > 5000) {
        console.log('数据更新似乎已停止，尝试重新获取...');
        fetchInitialData();
      }
    }, 5000);
    
    return () => {
      window.removeEventListener('apiData', handleApiData);
      clearInterval(checkUpdateTimer);
    };
  }, [lastUpdate]);

  return (
    <div className="dashboard-container">
      <div className="total-value-card">
        <h2>OKX 交易系统</h2>
        <p>实时监控您的交易账户</p>
        {lastUpdate && <p className="last-update">最后更新: {lastUpdate}</p>}
        
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
      </div>
    </div>
  );
}

export default HomePage;