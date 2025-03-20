import React, { useState, useEffect } from 'react';

function AccountPage() {
  const [accountData, setAccountData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 修改事件名称从wsData为apiData
    const handleApiData = (event) => {
      if (event.detail && event.detail.type === 'update' && event.detail.data.account) {
        setAccountData(event.detail.data.account);
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
          setLoading(false);
        }
      } catch (error) {
        console.error('获取初始数据失败:', error);
      }
    };
    
    fetchInitialData();
    
    return () => {
      window.removeEventListener('apiData', handleApiData);
    };
  }, []);

  if (loading) {
    return <div className="loading">加载账户数据中...</div>;
  }

  if (!accountData) {
    return <div className="page-container">
      <h2 className="page-header">账户信息</h2>
      <div>无可用账户数据</div>
    </div>;
  }

  return (
    <div className="page-container">
      <h2 className="page-header">账户信息</h2>
      
      <div className="account-info">
        <div className="total-value">
          <h3>总资产</h3>
          <div className="total-amount">{accountData.totalEq || '0'}</div>
        </div>
        
        <div className="assets-list">
          <h3>资产明细</h3>
          <div className="assets-grid">
            {accountData.details && accountData.details.map((item, index) => (
              <div className="asset-card" key={index}>
                <h4>{item.ccy}</h4>
                <div className="asset-details">
                  <p>可用: {item.availBal}</p>
                  <p>冻结: {item.frozenBal}</p>
                  <p>总额: {item.cashBal}</p>
                </div>
              </div>
            ))}
            {(!accountData.details || accountData.details.length === 0) && (
              <div>暂无资产明细</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default AccountPage;